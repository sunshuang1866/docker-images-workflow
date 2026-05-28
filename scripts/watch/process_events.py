#!/usr/bin/env python3
"""
Issue 监控 + 命令处理 — Label 驱动状态机

状态持久化: GitHub Issue Labels (ai-*)
每个 Issue 用 1 个 ai-* label 标记当前阶段+状态

状态流转:
  无 ai-* 标签 → dispatch init
  ai-pending    → init job 会自动 dispatch phase1
  ai-phase1-done + /accept → dispatch phase2
  ai-phase2-done + /accept → dispatch phase3
  ai-phase3-done + /accept → 标记完成
  ai-phase*-fail + /retry → dispatch 对应 phase
  ai-phase*-fail + /skip  → dispatch 下一 phase

命令检测安全网: 对比 label 状态与命令语义, 避免重复 dispatch
  例: label=ai-phase1-done, 命令=/accept → dispatch phase2 ✓
      label=ai-phase2,      命令=/accept → 已处理, 跳过 ✓
"""

import os
import sys
import re
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
WATCHLIST_FILE = os.path.join(PROJECT_ROOT, 'config', 'watchlist.json')

LABEL_REGEX = re.compile(r'^ai-(phase[123]|done|pending)(?:-(done|fail))?$')

NEXT_PHASE = {'phase1': 'phase2', 'phase2': 'phase3', 'phase3': 'done'}
VALID_COMMANDS = ['/accept', '/retry', '/skip',
                  '/retry-phase1', '/retry-phase2', '/retry-phase3']


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def get_headers(token: str) -> Dict[str, str]:
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


# ── Label 解析（自包含，不依赖 issue_tracker 模块） ──

def parse_phase_from_labels(labels: List[str]) -> Optional[Dict[str, str]]:
    """返回 {'phase': 'phase1', 'status': 'done'} 或 None"""
    for label in labels:
        m = LABEL_REGEX.match(label)
        if m:
            phase = m.group(1)
            status = m.group(2) or 'running'
            return {'phase': phase, 'status': status, 'label': label}
    return None


def is_tracked(labels: List[str]) -> bool:
    return any(l.startswith('ai-') for l in labels)


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


def fetch_recent_comments(repo: str, issue_number: int, token: str,
                          count: int = 10) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    params = {'per_page': count, 'sort': 'created', 'direction': 'desc'}
    try:
        resp = requests.get(url, headers=get_headers(token), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"  ❌ Comments for #{issue_number}: {e}")
        return []


# ── 命令解析 ──

def parse_command_from_comments(comments: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """从评论列表中查找最新的有效命令"""
    for comment in sorted(comments, key=lambda c: c.get('created_at', ''), reverse=True):
        body = (comment.get('body') or '').strip()
        first_line = body.split('\n')[0].strip()
        for cmd in VALID_COMMANDS:
            if first_line.startswith(cmd):
                return {
                    'command': cmd,
                    'comment_id': str(comment['id']),
                    'comment_user': comment.get('user', {}).get('login', ''),
                    'created_at': comment.get('created_at', ''),
                }
    return None


def should_apply_command(command: str, label_state: Optional[Dict[str, str]]) -> Optional[str]:
    """
    判断命令是否应该执行, 返回目标 phase 或 None

    label_state: {'phase': 'phase1', 'status': 'done'} 或 None (未追踪)

    安全网: 如果 label 状态已经反映了命令的结果, 返回 None 避免重复
    """
    if label_state is None:
        return None

    current = label_state['phase']
    status = label_state['status']

    if current == 'done':
        return None

    # /accept: 仅在当前阶段 done 时推进到下一阶段
    if command == '/accept':
        if status == 'done':
            return NEXT_PHASE.get(current)
        # label 还是 running/fail → 还没 done, /accept 无效
        return None

    # /retry: 仅在当前阶段 failed 时重跑
    if command == '/retry':
        if status == 'fail':
            return current
        return None

    # /skip: 仅在当前阶段 failed 或 done 时跳过
    if command == '/skip':
        if status in ('fail', 'done'):
            nxt = NEXT_PHASE.get(current)
            return nxt or 'done'
        return None

    # /retry-phase{1,2,3}: 显式重跑任意阶段, 无条件
    if command == '/retry-phase1':
        return 'phase1'
    if command == '/retry-phase2':
        return 'phase2'
    if command == '/retry-phase3':
        return 'phase3'

    return None


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
        trigger_labels = repo_config.get('trigger_labels', ['feature', 'bug'])

        if not repo_config.get('enabled', True):
            continue

        log(f"\n{'='*60}")
        log(f"📦 {repo}")

        issues = fetch_issues_with_labels(repo, trigger_labels, watch_token, max_events)

        new_count = 0
        tracked_issues = []
        for issue in issues:
            labels = [l['name'] for l in issue.get('labels', [])]

            if is_tracked(labels):
                tracked_issues.append(issue)
                continue

            new_count += 1
            log(f"  🆕 #{issue['number']}: {issue.get('title', '')} → dispatching init")
            dispatch_phase(repo, issue, 'init', dispatch_token)

        if new_count > 0:
            log(f"  📦 New issues dispatched: {new_count}")
        log(f"  📋 Tracked issues to check for commands: {len(tracked_issues)}")

        # ── 检查已追踪 Issue 上的命令 ──
        _check_commands_on_tracked_issues(repo, tracked_issues, watch_token, dispatch_token)

    log(f"\n✅ Cycle complete.")


def _check_commands_on_tracked_issues(repo: str, issues: List[Dict[str, Any]],
                                       watch_token: str, dispatch_token: str):
    if not issues:
        return

    log(f"  📝 Checking commands...")

    for issue in issues:
        issue_number = issue['number']
        labels = [l['name'] for l in issue.get('labels', [])]
        label_state = parse_phase_from_labels(labels)

        if label_state is None:
            continue

        if label_state['phase'] == 'pending' or label_state['status'] == 'running':
            continue

        comments = fetch_recent_comments(repo, issue_number, watch_token)
        command_info = parse_command_from_comments(comments)

        if not command_info:
            continue

        target = should_apply_command(command_info['command'], label_state)

        if target is None:
            log(f"    ⏭️  #{issue_number}: {command_info['command']} "
                f"(label={label_state['label']}, no-op)")
            continue

        log(f"    🔔 #{issue_number}: {command_info['command']} → {target} "
            f"(from {label_state['label']})")

        if target == 'done':
            log(f"    ✅ #{issue_number}: all phases complete")
            continue

        issue_data = {
            'number': issue['number'],
            'title': issue.get('title', ''),
            'body': issue.get('body') or '',
        }
        dispatch_phase(repo, issue_data, target, dispatch_token)


if __name__ == '__main__':
    process_all()
