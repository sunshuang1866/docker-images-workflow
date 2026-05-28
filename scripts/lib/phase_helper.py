#!/usr/bin/env python3
"""
phase_helper.py — workflow step 中的辅助操作

用法:
  python scripts/lib/phase_helper.py add-labels
  python scripts/lib/phase_helper.py post-board
  python scripts/lib/phase_helper.py update-board <phase> <status>
  python scripts/lib/phase_helper.py set-label <phase> <status>
  python scripts/lib/phase_helper.py ensure-labels
  python scripts/lib/phase_helper.py self-dispatch <phase>
"""

import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from scripts.lib.state_machine import (
    ALL_AI_LABELS,
    LABEL_COLORS,
    LABEL_DESCRIPTIONS,
    NEXT_PHASE,
    PHASE_DISPLAY,
    build_label,
)


def get_token():
    return os.getenv('GITHUB_TOKEN', '')


def get_headers():
    return {
        'Authorization': f'token {get_token()}',
        'Accept': 'application/vnd.github.v3+json',
    }


def get_params():
    source_repo = os.getenv('SOURCE_REPO', '')
    issue_number = os.getenv('ISSUE_NUMBER', '')
    issue_title = os.getenv('ISSUE_TITLE', '')
    issue_body = os.getenv('ISSUE_BODY', '')

    if not source_repo or not issue_number:
        event_path = os.getenv('GITHUB_EVENT_PATH', '')
        if event_path and os.path.exists(event_path):
            with open(event_path) as f:
                event = json.load(f)
            cp = event.get('client_payload', {})
            source_repo = source_repo or cp.get('source_repo', '')
            issue_number = issue_number or str(cp.get('issue_number', ''))
            issue_title = issue_title or cp.get('issue_title', '')
            issue_body = issue_body or cp.get('issue_body') or ''

    if not source_repo or not issue_number:
        raise RuntimeError(f'Cannot determine source_repo/issue_number. '
                           f'SOURCE_REPO={source_repo}, ISSUE_NUMBER={issue_number}')

    return {
        'source_repo': source_repo,
        'issue_number': issue_number,
        'issue_title': issue_title,
        'issue_body': issue_body,
    }


def split_repo(repo_full):
    parts = repo_full.split('/')
    return parts[0], parts[1]


def set_issue_label(owner: str, repo: str, issue_number: int, phase: str, status: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_headers(), timeout=30)
    resp.raise_for_status()
    current_labels = [l['name'] for l in resp.json().get('labels', [])]

    keep_labels = [l for l in current_labels if not l.startswith('ai-')]
    new_label = build_label(phase, status)
    keep_labels.append(new_label)

    labels_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    resp = requests.put(labels_url, headers=get_headers(),
                        json={'labels': keep_labels}, timeout=30)
    if resp.status_code == 200:
        print(f'✅ Label set: {new_label} (preserved: {[l for l in keep_labels if l != new_label]})')
    else:
        print(f'❌ Set label failed HTTP {resp.status_code}: {resp.text}')


def ensure_labels_exist(owner: str, repo: str):
    for label in ALL_AI_LABELS:
        url = f"https://api.github.com/repos/{owner}/{repo}/labels/{label}"
        try:
            resp = requests.get(url, headers=get_headers(), timeout=15)
            if resp.status_code == 200:
                continue
        except Exception:
            pass
        requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/labels",
            headers=get_headers(),
            json={
                'name': label,
                'color': LABEL_COLORS.get(label, 'bfd4f2'),
                'description': LABEL_DESCRIPTIONS.get(label, f'AI analysis: {label}'),
            },
            timeout=15,
        )
        print(f'  🏷️  Created label: {label}')


def cmd_add_labels():
    params = get_params()
    owner, repo = split_repo(params['source_repo'])
    issue_number = int(params['issue_number'])

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    resp = requests.get(url, headers=get_headers(), timeout=30)
    resp.raise_for_status()
    current_labels = [l['name'] for l in resp.json()]

    if 'ai-pending' in current_labels:
        print(f'⚠️  ai-pending already exists, skipping')
        return

    current_labels.append('ai-pending')
    resp = requests.put(url, headers=get_headers(),
                        json={'labels': current_labels}, timeout=30)
    if resp.status_code == 200:
        print(f'✅ Label added: ai-pending')
    else:
        print(f'❌ Add label failed HTTP {resp.status_code}: {resp.text}')


def cmd_set_label():
    if len(sys.argv) < 4:
        print('Usage: phase_helper.py set-label <phase> <status>')
        sys.exit(1)
    phase = sys.argv[2]
    status = sys.argv[3]

    params = get_params()
    owner, repo = split_repo(params['source_repo'])
    issue_number = int(params['issue_number'])

    set_issue_label(owner, repo, issue_number, phase, status)


def cmd_ensure_labels():
    params = get_params()
    owner, repo = split_repo(params['source_repo'])
    ensure_labels_exist(owner, repo)
    print(f'✅ All ai-* labels ensured in {owner}/{repo}')


def cmd_post_board():
    params = get_params()
    owner, repo = split_repo(params['source_repo'])
    issue_number = int(params['issue_number'])

    stages = {
        'req-analysis': 'in_progress',
        'arch-design': 'pending',
        'arch-review': 'pending',
    }
    _ensure_board(owner, repo, issue_number, params['issue_title'], params['source_repo'], stages)
    print(f'✅ Board posted to {owner}/{repo}#{issue_number}')


def cmd_update_board():
    if len(sys.argv) < 4:
        print('Usage: phase_helper.py update-board <phase> <status>')
        sys.exit(1)
    phase = sys.argv[2]
    status = sys.argv[3]

    params = get_params()
    owner, repo = split_repo(params['source_repo'])
    issue_number = int(params['issue_number'])

    stages = _read_board_stages(owner, repo, issue_number)
    stages[phase] = status

    if status == 'done':
        next_phase = NEXT_PHASE.get(phase)
        if next_phase and next_phase != 'done' and stages.get(next_phase, 'pending') == 'pending':
            stages[next_phase] = 'in_progress'

    _ensure_board(owner, repo, issue_number, params['issue_title'], params['source_repo'], stages)
    print(f'✅ Board updated: {phase} → {status}')

    set_issue_label(owner, repo, issue_number, phase, status)


def cmd_self_dispatch():
    if len(sys.argv) < 3:
        print('Usage: phase_helper.py self-dispatch <phase>')
        sys.exit(1)
    phase = sys.argv[2]

    params = get_params()
    target_repo = os.getenv('GITHUB_REPOSITORY', 'ZhengZhenyu/dev-workflow')

    url = f"https://api.github.com/repos/{target_repo}/dispatches"
    payload = {
        'event_type': 'run-phase',
        'client_payload': {
            'phase': phase,
            'source_repo': params['source_repo'],
            'issue_number': params['issue_number'],
            'issue_title': params['issue_title'],
            'issue_body': params['issue_body'],
        }
    }

    resp = requests.post(url, headers=get_headers(), json=payload, timeout=30)
    if resp.status_code == 204:
        print(f'✅ Self-dispatched: phase={phase} for #{params["issue_number"]}')
    else:
        print(f'❌ Self-dispatch failed HTTP {resp.status_code}: {resp.text}')
        sys.exit(1)


BOARD_MARKER = '🤖 tech-design-team · 分析进度'

BOARD_PHASE_MAP = {
    '需求分析': 'req-analysis',
    '架构设计': 'arch-design',
    '架构评审': 'arch-review',
}


def _find_board_comment(owner, repo, issue_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    params = {'per_page': 100, 'sort': 'created', 'direction': 'asc'}
    resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
    resp.raise_for_status()
    for comment in resp.json():
        if BOARD_MARKER in (comment.get('body') or ''):
            return comment
    return None


def _read_board_stages(owner, repo, issue_number):
    comment = _find_board_comment(owner, repo, issue_number)
    if not comment:
        return {'req-analysis': 'pending', 'arch-design': 'pending', 'arch-review': 'pending'}

    body = comment.get('body', '')
    status_emoji = {
        '🔄': 'in_progress', '✅': 'done', '❌': 'failed',
        '⬜': 'pending', '⏭️': 'skipped',
    }

    stages = {}

    for line in body.split('\n'):
        for display_name, phase_key in BOARD_PHASE_MAP.items():
            if display_name in line:
                for emoji, status_key in status_emoji.items():
                    if emoji in line:
                        stages[phase_key] = status_key
                        break
                else:
                    stages[phase_key] = 'pending'
                break

    for k in ['req-analysis', 'arch-design', 'arch-review']:
        if k not in stages:
            stages[k] = 'pending'

    return stages


def _build_board_body(issue_number, issue_title, source_repo, stages):
    status_map = {
        'in_progress': '🔄 进行中', 'done': '✅ 完成',
        'failed': '❌ 失败', 'pending': '⬜ -', 'skipped': '⏭️ 跳过',
    }

    def s(p):
        return status_map.get(stages.get(p, 'pending'), '⬜ -')

    return '\n'.join([
        '## 🤖 tech-design-team · 分析进度',
        '',
        f'**Issue**: #{issue_number} - {issue_title}',
        f'**来源仓库**: {source_repo}',
        '',
        '### 📊 分析进度',
        '',
        '| 阶段 | 状态 |',
        '|------|------|',
        f'| 需求分析 (req-analysis) | {s("req-analysis")} |',
        f'| 架构设计 (arch-design) | {s("arch-design")} |',
        f'| 架构评审 (arch-review) | {s("arch-review")} |',
        '',
        '### 🔧 控制命令',
        '',
        '| 命令 | 用途 |',
        '|------|------|',
        '| `/analyze` | 启动分析（未追踪的 Issue） |',
        '| `/accept` | 确认当前阶段，进入下一阶段 |',
        '| `/retry` | 重跑当前失败阶段 |',
        '| `/skip` | 跳过当前阶段 |',
        '| `/retry-req` | 重跑需求分析 |',
        '| `/retry-arch` | 重跑架构设计 |',
        '| `/retry-review` | 重跑架构评审 |',
    ])


def _ensure_board(owner, repo, issue_number, issue_title, source_repo, stages):
    body = _build_board_body(issue_number, issue_title, source_repo, stages)
    comment = _find_board_comment(owner, repo, issue_number)

    if comment:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment['id']}"
        resp = requests.patch(url, headers=get_headers(), json={'body': body}, timeout=30)
        resp.raise_for_status()
    else:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp = requests.post(url, headers=get_headers(), json={'body': body}, timeout=30)
        resp.raise_for_status()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''

    handlers = {
        'add-labels': cmd_add_labels,
        'set-label': cmd_set_label,
        'ensure-labels': cmd_ensure_labels,
        'post-board': cmd_post_board,
        'update-board': cmd_update_board,
        'self-dispatch': cmd_self_dispatch,
    }

    if cmd in handlers:
        handlers[cmd]()
    else:
        print(f'Unknown command: {cmd}')
        print('Available: add-labels | set-label | ensure-labels | post-board | update-board | self-dispatch')
        sys.exit(1)