#!/usr/bin/env python3
"""
Issue 监控 + 命令处理 — Label 驱动状态机

触发模式 (trigger_mode):
  label   — 传统模式: 有 trigger_labels 的 Issue 自动 dispatch init
  command — 命令模式: 仅当用户在 Issue 评论 /analyze 才触发
  both    — 混合模式: 同时支持 label 自动触发和 /analyze 命令触发

状态持久化: GitHub Issue Labels (ai-*)
每个 Issue 用 1 个 ai-* label 标记当前阶段+状态

状态流转:
  /analyze (未追踪) → dispatch init
  ai-pending → init 自动 dispatch req-analysis
  ai-req-analysis-done + /accept → dispatch arch-design
  ai-arch-design-done → 自动 dispatch arch-review (无需 /accept)
  ai-arch-review-done + /accept → 标记完成
  ai-*-fail + /retry → dispatch 对应 phase
  ai-*-fail + /skip → dispatch 下一 phase

Stuck 检测: running 状态超 60 分钟 → 自动标记 fail
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from scripts.lib.state_machine import (
    PhaseState,
    build_label,
    parse_phase_from_labels,
    is_tracked,
    should_apply_command,
    ALL_COMMANDS,
    ENTRY_COMMAND,
    PHASE_RETRY_COMMANDS,
    PHASE_DISPLAY,
    NEXT_PHASE,
    AUTO_ADVANCE,
    DESIGN_DONE_PHASE,
    build_label,
    STUCK_TIMEOUT_MINUTES,
)

WATCHLIST_FILE = os.path.join(PROJECT_ROOT, 'config', 'watchlist.json')


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def get_headers(token: str) -> Dict[str, str]:
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


# ── GitHub API ──

def fetch_issues_with_labels(repo: str, trigger_labels: List[str], token: str,
                             max_per_label: int = 50) -> List[Dict[str, Any]]:
    all_issues: List[Dict[str, Any]] = []
    seen: set = set()

    for label in trigger_labels:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            'state': 'open',
            'labels': label,
            'per_page': min(max_per_label, 100),
            'sort': 'updated',
            'direction': 'desc',
        }
        try:
            resp = requests.get(url, headers=get_headers(token), params=params, timeout=30)
            resp.raise_for_status()
            for issue in resp.json():
                if 'pull_request' in issue:
                    continue
                if issue['id'] not in seen:
                    seen.add(issue['id'])
                    all_issues.append(issue)
            log(f"  ✅ Label '{label}': Found {len(resp.json())} issues")
        except Exception as e:
            log(f"  ❌ Label '{label}' failed: {e}")

    log(f"  📊 Total unique open issues: {len(all_issues)}")
    return all_issues


def fetch_all_open_issues(repo: str, token: str, max_issues: int = 50) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo}/issues"
    params = {
        'state': 'open',
        'per_page': min(max_issues, 100),
        'sort': 'updated',
        'direction': 'desc',
    }
    try:
        resp = requests.get(url, headers=get_headers(token), params=params, timeout=30)
        resp.raise_for_status()
        issues = [i for i in resp.json() if 'pull_request' not in i]
        log(f"  📊 Total open issues: {len(issues)}")
        return issues
    except Exception as e:
        log(f"  ❌ Fetch issues failed: {e}")
        return []


def fetch_all_comments(repo: str, issue_number: int, token: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    params = {'per_page': 100, 'sort': 'created', 'direction': 'asc', 'page': 1}
    all_comments: List[Dict[str, Any]] = []
    while True:
        try:
            resp = requests.get(url, headers=get_headers(token), params=params, timeout=30)
            resp.raise_for_status()
            page_data = resp.json()
            if not page_data:
                break
            all_comments.extend(page_data)
            if len(page_data) < params['per_page']:
                break
            params['page'] += 1
        except Exception as e:
            log(f"  ❌ Comments for #{issue_number} (page {params['page']}): {e}")
            break
    log(f"  💬 #{issue_number}: fetched {len(all_comments)} total comments")
    return all_comments


# ── 命令解析 ──

def _find_command_in_body(body: str, commands: List[str]) -> Optional[str]:
    for line in body.split('\n'):
        stripped = line.strip()
        for cmd in commands:
            if stripped.startswith(cmd):
                return cmd
    return None


BOT_ACK_MARKER = '🤖 tech-design-team · 命令确认'


def _post_command_ack(repo: str, issue_number: int, command: str, target: str,
                      from_label: str, token: str):
    owner, name = repo.split('/')
    comment_url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments"
    body = f"{BOT_ACK_MARKER}\n\n> 命令 `{command}` 已处理: `{from_label}` → `{target}`"
    requests.post(comment_url, headers=get_headers(token), json={'body': body}, timeout=30)


def _find_last_ack_timestamp(comments: List[Dict[str, Any]]) -> Optional[str]:
    for comment in reversed(comments):
        body = (comment.get('body') or '')
        if BOT_ACK_MARKER in body:
            return comment.get('created_at', '')
    return None


def parse_command_from_comments(comments: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    ack_ts = _find_last_ack_timestamp(comments)
    for comment in sorted(comments, key=lambda c: c.get('created_at', ''), reverse=True):
        body = (comment.get('body') or '').strip()
        if not body:
            continue
        comment_ts = comment.get('created_at', '')
        if ack_ts and comment_ts and comment_ts <= ack_ts:
            continue
        cmd = _find_command_in_body(body, ALL_COMMANDS)
        if cmd:
            return {
                'command': cmd,
                'comment_id': str(comment['id']),
                'comment_user': comment.get('user', {}).get('login', ''),
                'created_at': comment_ts,
            }
    return None


def has_entry_command(comments: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    for comment in sorted(comments, key=lambda c: c.get('created_at', ''), reverse=True):
        body = (comment.get('body') or '').strip()
        if not body:
            continue
        if _find_command_in_body(body, [ENTRY_COMMAND]):
            return {
                'comment_id': str(comment['id']),
                'comment_user': comment.get('user', {}).get('login', ''),
                'created_at': comment.get('created_at', ''),
            }
    return None


# ── Stuck 检测 ──

def check_stuck_phase(issue: Dict[str, Any], label_state: PhaseState) -> bool:
    if not label_state.is_running or label_state.phase == DESIGN_DONE_PHASE:
        return False
    updated_at = issue.get('updated_at', '')
    if not updated_at:
        return False
    try:
        updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed = (now - updated_time).total_seconds() / 60
        if elapsed > STUCK_TIMEOUT_MINUTES:
            log(f"  ⚠️ #{issue['number']}: stuck in {label_state.label} for {elapsed:.0f} min")
            return True
    except Exception:
        pass
    return False


# ── Dispatch ──

def dispatch_phase(repo: str, issue: Dict[str, Any], phase: str, token: str) -> bool:
    target_repo = os.getenv('GITHUB_REPOSITORY', '') or 'ZhengZhenyu/dev-workflow'

    payload = {
        'event_type': 'run-phase',
        'client_payload': {
            'phase': phase,
            'source_repo': repo,
            'issue_number': issue['number'],
            'issue_title': issue.get('title', ''),
            'issue_body': issue.get('body') or '',
        }
    }

    url = f"https://api.github.com/repos/{target_repo}/dispatches"
    try:
        resp = requests.post(url, headers=get_headers(token), json=payload, timeout=30)
        if resp.status_code == 204:
            log(f"  ✅ Dispatched: phase={phase} for #{issue['number']}")
            return True
        else:
            log(f"  ❌ Dispatch failed HTTP {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log(f"  ❌ Dispatch error: {e}")
        return False


def set_label_on_issue(owner: str, name: str, issue_number: int, new_label: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}"
    resp = requests.get(url, headers=get_headers(token), timeout=30)
    resp.raise_for_status()
    current_labels = [l['name'] for l in resp.json().get('labels', [])]

    keep_labels = [l for l in current_labels if not l.startswith('ai-')]
    keep_labels.append(new_label)

    labels_url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/labels"
    requests.put(labels_url, headers=get_headers(token), json={'labels': keep_labels}, timeout=30)
    log(f"  🏷️ #{issue_number}: → {new_label}")


def mark_issue_stuck(repo: str, issue_number: int, label_state: PhaseState, token: str):
    owner, name = repo.split('/')
    new_label = build_label(label_state.phase, 'fail')
    set_label_on_issue(owner, name, issue_number, new_label, token)

    comment_url = f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments"
    body = f"⚠️ **Stuck detection**: {PHASE_DISPLAY.get(label_state.phase, label_state.phase)} "
    body += f"运行超时 ({STUCK_TIMEOUT_MINUTES} min)，已自动标记为失败。\n"
    body += f"请使用 `/retry` 重跑，或 `/skip` 跳过此阶段。"
    requests.post(comment_url, headers=get_headers(token), json={'body': body}, timeout=30)

    log(f"  🏷️ #{issue_number}: {label_state.label} → ai-{label_state.phase}-fail (stuck)")
    return build_label(label_state.phase, 'fail')


# ── 主流程 ──

def process_all():
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        watchlist = json.load(f)

    watch_token = os.getenv('WATCH_TOKEN') or os.getenv('DISPATCH_TOKEN', '')
    dispatch_token = os.getenv('DISPATCH_TOKEN', '')

    if not watch_token:
        log("❌ WATCH_TOKEN or DISPATCH_TOKEN not set")
        sys.exit(1)

    max_events = watchlist.get('settings', {}).get('max_events_per_run', 50)
    test_repo = os.getenv('TEST_REPO', '')

    log("🔍 Starting monitoring cycle")
    log(f"   WATCH_TOKEN: {'Yes' if watch_token else 'No'}")
    log(f"   DISPATCH_TOKEN: {'Yes' if dispatch_token else 'No'}")
    if test_repo:
        log(f"   Test mode: {test_repo}")

    repos = watchlist.get('watched_repos', [])
    if test_repo:
        repos = [r for r in repos if r['repo'] == test_repo]
        if not repos:
            log(f"❌ Test repo '{test_repo}' not in watchlist")
            sys.exit(1)

    for repo_config in repos:
        repo = repo_config['repo']
        trigger_labels = repo_config.get('trigger_labels', [])
        trigger_mode = repo_config.get('trigger_mode', 'label')

        if not repo_config.get('enabled', True):
            continue

        log(f"\n{'='*60}")
        log(f"📦 {repo} (mode={trigger_mode})")

        issues = _fetch_issues_by_mode(repo, trigger_labels, trigger_mode, watch_token, max_events)

        new_count = 0
        tracked_issues = []

        for issue in issues:
            labels = [l['name'] for l in issue.get('labels', [])]

            if is_tracked(labels):
                tracked_issues.append(issue)
                continue

            if trigger_mode == 'label':
                new_count += 1
                log(f"  🆕 #{issue['number']}: {issue.get('title', '')} → dispatching init")
                dispatch_phase(repo, issue, 'init', dispatch_token)
                continue

            if trigger_mode in ('command', 'both'):
                comments = fetch_all_comments(repo, issue['number'], watch_token)
                entry = has_entry_command(comments)
                if entry:
                    new_count += 1
                    log(f"  🆕 #{issue['number']}: /analyze by {entry['comment_user']} → dispatching init")
                    dispatch_phase(repo, issue, 'init', dispatch_token)
                else:
                    log(f"  ⏭️ #{issue['number']}: no /analyze command, skip")
                continue

        if new_count > 0:
            log(f"  📦 New issues dispatched: {new_count}")
        log(f"  📋 Tracked issues to check: {len(tracked_issues)}")

        _check_commands_on_tracked_issues(repo, tracked_issues, watch_token, dispatch_token)

    log(f"\n✅ Cycle complete.")


def _fetch_issues_by_mode(repo: str, trigger_labels: List[str], trigger_mode: str,
                          token: str, max_events: int) -> List[Dict[str, Any]]:
    if trigger_mode == 'command' and not trigger_labels:
        return fetch_all_open_issues(repo, token, max_events)

    if trigger_mode == 'command' and trigger_labels:
        issues = fetch_issues_with_labels(repo, trigger_labels, token, max_events)
        extra = fetch_all_open_issues(repo, token, max_events)
        seen = {i['id'] for i in issues}
        for i in extra:
            if i['id'] not in seen:
                issues.append(i)
                seen.add(i['id'])
        return issues

    return fetch_issues_with_labels(repo, trigger_labels, token, max_events)


def _check_commands_on_tracked_issues(repo: str, issues: List[Dict[str, Any]],
                                       watch_token: str, dispatch_token: str):
    if not issues:
        return

    log(f"  📝 Checking commands + stuck detection...")

    for issue in issues:
        issue_number = issue['number']
        labels = [l['name'] for l in issue.get('labels', [])]
        label_state = parse_phase_from_labels(labels)

        if label_state.phase is None and label_state.status == 'pending':
            continue

        if label_state.is_running:
            if check_stuck_phase(issue, label_state):
                mark_issue_stuck(repo, issue_number, label_state, watch_token)
            continue

        if label_state.is_done and label_state.phase not in (None, DESIGN_DONE_PHASE):
            if AUTO_ADVANCE.get(label_state.phase, False):
                target = NEXT_PHASE.get(label_state.phase)
                if target == DESIGN_DONE_PHASE:
                    log(f"    ✅ #{issue_number}: {label_state.phase} done → all design phases complete → marking ai-design-done")
                    owner, name = repo.split('/')
                    new_label = build_label(DESIGN_DONE_PHASE, 'done')
                    set_label_on_issue(owner, name, issue_number, new_label, watch_token)
                elif target:
                    log(f"    🔄 #{issue_number}: {label_state.phase} done → auto-advance fallback to {target}")
                    issue_data = {
                        'number': issue['number'],
                        'title': issue.get('title', ''),
                        'body': issue.get('body') or '',
                    }
                    dispatch_phase(repo, issue_data, target, dispatch_token)
                continue
            # AUTO_ADVANCE=False: fall through to command check below

        comments = fetch_all_comments(repo, issue_number, watch_token)
        command_info = parse_command_from_comments(comments)

        if not command_info:
            continue

        target = should_apply_command(command_info['command'], label_state)

        if target is None:
            log(f"    ⏭️ #{issue_number}: {command_info['command']} "
                f"(label={label_state.label}, no-op)")
            continue

        log(f"    🔔 #{issue_number}: {command_info['command']} → {target} "
            f"(from {label_state.label})")

        if target == DESIGN_DONE_PHASE:
            log(f"    ✅ #{issue_number}: all design phases complete → marking ai-design-done")
            owner, name = repo.split('/')
            new_label = build_label(DESIGN_DONE_PHASE, 'done')
            set_label_on_issue(owner, name, issue_number, new_label, watch_token)
            _post_command_ack(repo, issue_number, command_info['command'], target, label_state.label, watch_token)
            continue

        issue_data = {
            'number': issue['number'],
            'title': issue.get('title', ''),
            'body': issue.get('body') or '',
        }
        dispatch_phase(repo, issue_data, target, dispatch_token)
        _post_command_ack(repo, issue_number, command_info['command'], target, label_state.label, watch_token)


if __name__ == '__main__':
    process_all()