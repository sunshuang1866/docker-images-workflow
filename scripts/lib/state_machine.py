#!/usr/bin/env python3
"""
Workflow 状态机 — 唯一权威定义

所有模块（process_events, issue_tracker, phase_helper, workflow YAML）
必须引用此模块，不得各自重复定义。

Phase 语义化命名:
  req-analysis   需求分析（原 phase1）
  arch-design    架构设计（原 phase2）
  arch-review    架构评审（原 phase3）

Label 体系:
  ai-pending                 初始状态
  ai-req-analysis            需求分析进行中
  ai-req-analysis-done       需求分析完成
  ai-req-analysis-fail       需求分析失败
  ai-arch-design             架构设计进行中
  ai-arch-design-done        架构设计完成
  ai-arch-design-fail        架构设计失败
  ai-arch-review             架构评审进行中
  ai-arch-review-done       架构评审完成
  ai-arch-review-fail       架构评审失败
  ai-design-done            设计流程完成（等待人工确认或开发）

命令体系:
  /analyze          入口命令：触发全流程（命令触发模式下使用）
  /accept           确认当前阶段完成，进入下一阶段
  /retry            重跑当前失败阶段，或在 design-done 状态下重跑架构评审
  /skip             跳过当前失败/完成阶段
  /retry-req        重跑需求分析
  /retry-arch       重跑架构设计
  /retry-review     重跑架构评审
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass

PHASES = ['req-analysis', 'arch-design', 'arch-review']

PHASE_DISPLAY = {
    'req-analysis': '需求分析',
    'arch-design': '架构设计',
    'arch-review': '架构评审',
}

PHASE_STAGE_FILE = {
    'req-analysis': '01-requirements-analysis',
    'arch-design': '02-architecture-design',
    'arch-review': '03-architecture-review',
}

NEXT_PHASE = {
    'req-analysis': 'arch-design',
    'arch-design': 'arch-review',
    'arch-review': 'design-done',
}

DESIGN_DONE_PHASE = 'design-done'

PHASE_LABEL_REGEX = r'^(req-analysis|arch-design|arch-review)$'

LABEL_REGEX = re.compile(
    r'^ai-(pending|design-done|req-analysis|arch-design|arch-review)(?:-(done|fail))?$'
)

STATUSES = ['pending', 'running', 'done', 'fail']

ALL_AI_LABELS = [
    'ai-pending',
    'ai-req-analysis', 'ai-req-analysis-done', 'ai-req-analysis-fail',
    'ai-arch-design', 'ai-arch-design-done', 'ai-arch-design-fail',
    'ai-arch-review', 'ai-arch-review-done', 'ai-arch-review-fail',
    'ai-design-done',
]

LABEL_COLORS = {
    'ai-pending': 'bfd4f2',
    'ai-req-analysis': '0052cc',
    'ai-req-analysis-done': '0e8a16',
    'ai-req-analysis-fail': 'd73a4a',
    'ai-arch-design': '0052cc',
    'ai-arch-design-done': '0e8a16',
    'ai-arch-design-fail': 'd73a4a',
    'ai-arch-review': '0052cc',
    'ai-arch-review-done': '0e8a16',
    'ai-arch-review-fail': 'd73a4a',
    'ai-design-done': '5319e7',
}

LABEL_DESCRIPTIONS = {
    'ai-pending': 'AI 分析: 等待处理',
    'ai-req-analysis': 'AI 分析: 需求分析进行中',
    'ai-req-analysis-done': 'AI 分析: 需求分析完成',
    'ai-req-analysis-fail': 'AI 分析: 需求分析失败',
    'ai-arch-design': 'AI 分析: 架构设计进行中',
    'ai-arch-design-done': 'AI 分析: 架构设计完成',
    'ai-arch-design-fail': 'AI 分析: 架构设计失败',
    'ai-arch-review': 'AI 分析: 架构评审进行中',
    'ai-arch-review-done': 'AI 分析: 架构评审完成',
    'ai-arch-review-fail': 'AI 分析: 架构评审失败',
    'ai-design-done': 'AI 分析: 设计流程完成',
}

ENTRY_COMMAND = '/analyze'

FLOW_COMMANDS = ['/accept', '/retry', '/skip']

PHASE_RETRY_COMMANDS = {
    '/retry-req': 'req-analysis',
    '/retry-arch': 'arch-design',
    '/retry-review': 'arch-review',
}

ALL_COMMANDS = [ENTRY_COMMAND] + FLOW_COMMANDS + list(PHASE_RETRY_COMMANDS.keys())

AUTO_ADVANCE = {'init': True, 'req-analysis': False, 'arch-design': True}

TRIGGER_MODES = ['label', 'command', 'both']

STUCK_TIMEOUT_MINUTES = 60


@dataclass
class PhaseState:
    phase: Optional[str]
    status: Optional[str]
    label: Optional[str]

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


def build_label(phase: str, status: str) -> str:
    if phase == DESIGN_DONE_PHASE:
        return 'ai-design-done'
    if status == 'running':
        return f'ai-{phase}'
    return f'ai-{phase}-{status}'


def parse_phase_from_labels(labels: List[str]) -> PhaseState:
    for label in labels:
        if label == 'ai-pending':
            return PhaseState(phase=None, status='pending', label=label)
        if label == 'ai-design-done':
            return PhaseState(phase=DESIGN_DONE_PHASE, status='done', label=label)
        m = LABEL_REGEX.match(label)
        if m:
            phase = m.group(1)
            status = m.group(2) or 'running'
            return PhaseState(phase=phase, status=status, label=label)
    return PhaseState(phase=None, status=None, label=None)


def is_tracked(labels: List[str]) -> bool:
    return any(l.startswith('ai-') for l in labels)


def should_apply_command(command: str, label_state: Optional[PhaseState]) -> Optional[str]:
    """
    判断命令是否应执行，返回目标 phase 或 None。

    安全网: label 状态已反映命令结果时返回 None，避免重复 dispatch。
    """
    if label_state is None or not label_state.is_tracked:
        return None

    current = label_state.phase
    status = label_state.status

    if current == DESIGN_DONE_PHASE:
        if command == '/retry':
            return 'arch-review'
        return None

    if command == '/accept':
        if status == 'done':
            return NEXT_PHASE.get(current)
        return None

    if command == '/retry':
        if status == 'fail':
            return current
        if current == 'arch-review' and status == 'done':
            return 'arch-design'
        return None

    if command == '/skip':
        if status in ('fail', 'done'):
            nxt = NEXT_PHASE.get(current)
            return nxt or DESIGN_DONE_PHASE
        return None

    if command in PHASE_RETRY_COMMANDS:
        return PHASE_RETRY_COMMANDS[command]

    return None