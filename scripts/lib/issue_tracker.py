#!/usr/bin/env python3
"""
Issue 状态追踪 — 使用 GitHub Labels 持久化

所有常量和类型定义来自 state_machine 模块，此文件仅提供 GitHub API 操作。
"""

import os
import requests
from typing import List, Dict, Any

from scripts.lib.state_machine import (
    PhaseState,
    ALL_AI_LABELS,
    LABEL_COLORS,
    LABEL_DESCRIPTIONS,
    NEXT_PHASE,
    PHASE_DISPLAY,
    parse_phase_from_labels,
    build_label,
    is_tracked,
)


def get_api_headers() -> Dict[str, str]:
    token = os.getenv('WATCH_TOKEN') or os.getenv('DISPATCH_TOKEN') or os.getenv('GITHUB_TOKEN', '')
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


def read_issue_phase(owner: str, repo: str, issue_number: int) -> PhaseState:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    labels = [l['name'] for l in resp.json().get('labels', [])]
    return parse_phase_from_labels(labels)


def set_issue_phase(owner: str, repo: str, issue_number: int, phase: str, status: str) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    current_labels = [l['name'] for l in resp.json().get('labels', [])]

    keep_labels = [l for l in current_labels if not l.startswith('ai-')]
    new_label = build_label(phase, status)
    keep_labels.append(new_label)

    labels_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    resp = requests.put(labels_url, headers=get_api_headers(),
                        json={'labels': keep_labels}, timeout=30)
    if resp.status_code == 200:
        print(f"  ✅ Labels: → {keep_labels}")
        return True
    else:
        print(f"  ❌ Set labels failed HTTP {resp.status_code}: {resp.text}")
        return False


def is_issue_tracked(labels: List[str]) -> bool:
    return is_tracked(labels)


def should_skip_issue(labels: List[str]) -> bool:
    return 'ai-design-done' in labels


def get_ai_labels_on_issue(owner: str, repo: str, issue_number: int) -> List[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    return [l['name'] for l in resp.json().get('labels', []) if l['name'].startswith('ai-')]


def ensure_labels_exist(owner: str, repo: str):
    for label in ALL_AI_LABELS:
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        try:
            resp = requests.get(f"{url}/{label}", headers=get_api_headers(), timeout=15)
            if resp.status_code == 200:
                continue
        except Exception:
            pass

        requests.post(url, headers=get_api_headers(),
                      json={
                          'name': label,
                          'color': LABEL_COLORS.get(label, 'bfd4f2'),
                          'description': LABEL_DESCRIPTIONS.get(label, f'AI analysis: {label}'),
                      }, timeout=15)
        print(f"  🏷️  Created label: {label}")