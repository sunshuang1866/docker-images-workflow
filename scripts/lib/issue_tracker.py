#!/usr/bin/env python3
"""
Issue 状态追踪 — 使用 GitHub Labels 持久化

Label 命名约定:
  ai-pending        初始状态，等待处理
  ai-phase1         Phase 1 进行中
  ai-phase1-done    Phase 1 完成
  ai-phase1-fail    Phase 1 失败
  ai-phase2         Phase 2 进行中
  ai-phase2-done    Phase 2 完成
  ai-phase2-fail    Phase 2 失败
  ai-phase3         Phase 3 进行中
  ai-phase3-done    Phase 3 完成
  ai-phase3-fail    Phase 3 失败
  ai-done           全部完成

状态读取: 检查 Issue 上是否有 ai-* 标签 → 解析 phase + status
状态写入: 移除旧 ai-* 标签 + 添加新 ai-{phase}[-{status}] 标签
"""

import os
import re
import requests
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

ALL_AI_LABELS = [
    'ai-pending',
    'ai-phase1', 'ai-phase1-done', 'ai-phase1-fail',
    'ai-phase2', 'ai-phase2-done', 'ai-phase2-fail',
    'ai-phase3', 'ai-phase3-done', 'ai-phase3-fail',
    'ai-done',
]

LABEL_REGEX = re.compile(r'^ai-(phase[123])(?:-(done|fail))?$')

NEXT_PHASE = {'phase1': 'phase2', 'phase2': 'phase3', 'phase3': 'done'}


@dataclass
class PhaseState:
    phase: Optional[str]    # 'phase1' | 'phase2' | 'phase3' | None (未追踪)
    status: Optional[str]   # 'running' | 'done' | 'fail' | None
    label: Optional[str]    # 原始 label 名，如 'ai-phase2-done'

    @property
    def is_done(self) -> bool:
        return self.status == 'done'

    @property
    def is_running(self) -> bool:
        return self.status == 'running'

    @property
    def is_failed(self) -> bool:
        return self.status == 'fail'

    @property
    def is_tracked(self) -> bool:
        return self.phase is not None


def get_api_headers() -> Dict[str, str]:
    token = os.getenv('WATCH_TOKEN') or os.getenv('DISPATCH_TOKEN') or os.getenv('GITHUB_TOKEN', '')
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


def parse_phase_from_labels(labels: List[str]) -> PhaseState:
    """从 Issue 的 label 列表中解析当前阶段状态"""
    for label in labels:
        if label == 'ai-pending':
            return PhaseState(phase=None, status='pending', label=label)
        if label == 'ai-done':
            return PhaseState(phase='done', status='done', label=label)
        m = LABEL_REGEX.match(label)
        if m:
            phase = m.group(1)
            status = m.group(2) or 'running'
            return PhaseState(phase=phase, status=status, label=label)
    return PhaseState(phase=None, status=None, label=None)


def build_label(phase: str, status: str) -> str:
    """构建 label 名，如 build_label('phase2', 'done') → 'ai-phase2-done'"""
    if phase == 'done':
        return 'ai-done'
    if status == 'running':
        return f'ai-{phase}'
    return f'ai-{phase}-{status}'


def read_issue_phase(owner: str, repo: str, issue_number: int) -> PhaseState:
    """读取 Issue 当前阶段（HTTP GET）"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    labels = [l['name'] for l in resp.json().get('labels', [])]
    return parse_phase_from_labels(labels)


def set_issue_phase(owner: str, repo: str, issue_number: int, phase: str, status: str) -> bool:
    """
    设置 Issue 阶段状态。
    先移除所有旧的 ai-* 标签，再添加新标签。

    示例:
      set_issue_phase('opensourceways', 'community-health', 3, 'phase2', 'running')
      → Issue 被标为 ai-phase2

      set_issue_phase('opensourceways', 'community-health', 3, 'phase2', 'done')
      → Issue 被标为 ai-phase2-done
    """
    # 1. 获取当前 labels
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    current_labels = [l['name'] for l in resp.json().get('labels', [])]

    # 2. 只移除 ai-* 标签，保留用户的 feature/bug/... 标签
    keep_labels = [l for l in current_labels if not l.startswith('ai-')]
    new_label = build_label(phase, status)
    keep_labels.append(new_label)

    # 3. 用新标签列表替换
    labels_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
    resp = requests.put(labels_url, headers=get_api_headers(),
                        json={'labels': keep_labels}, timeout=30)
    if resp.status_code == 200:
        print(f"  ✅ Labels: → {keep_labels}")
        return True
    else:
        print(f"  ❌ Set labels failed HTTP {resp.status_code}: {resp.text}")
        return False


# ── 便捷方法（集成到 process_events.py 用） ──

def is_issue_tracked(labels: List[str]) -> bool:
    """判断 Issue 是否已被追踪（有任何 ai- 标签）"""
    return any(l.startswith('ai-') for l in labels)


def should_skip_issue(labels: List[str]) -> bool:
    """判断是否跳过（已关闭 / 已完成）"""
    return 'ai-done' in labels


def get_ai_labels_on_issue(owner: str, repo: str, issue_number: int) -> List[str]:
    """获取 Issue 上所有 ai-* 标签"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    resp = requests.get(url, headers=get_api_headers(), timeout=30)
    resp.raise_for_status()
    return [l['name'] for l in resp.json().get('labels', []) if l['name'].startswith('ai-')]


def ensure_labels_exist(owner: str, repo: str):
    """确保源仓库中存在所有 ai-* 标签（不存在则创建）"""
    for label in ALL_AI_LABELS:
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        try:
            resp = requests.get(f"{url}/{label}", headers=get_api_headers(), timeout=15)
            if resp.status_code == 200:
                continue
        except Exception:
            pass

        color_map = {
            'ai-pending': 'bfd4f2',
            'ai-phase1': '0052cc', 'ai-phase1-done': '0e8a16', 'ai-phase1-fail': 'd73a4a',
            'ai-phase2': '0052cc', 'ai-phase2-done': '0e8a16', 'ai-phase2-fail': 'd73a4a',
            'ai-phase3': '0052cc', 'ai-phase3-done': '0e8a16', 'ai-phase3-fail': 'd73a4a',
            'ai-done': '5319e7',
        }

        requests.post(url, headers=get_api_headers(),
                      json={'name': label, 'color': color_map.get(label, 'bfd4f2'),
                            'description': f'AI analysis: {label}'}, timeout=15)
        print(f"  🏷️  Created label: {label}")
