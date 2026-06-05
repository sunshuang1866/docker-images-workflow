#!/usr/bin/env python3
"""
ci-data 分支读写工具

ci-data 分支结构：
  ci-fix/{pr_number}/ci-analysis.md       — CI 失败分析报告（完整，无截断）
  ci-fix/{pr_number}/code-fix-summary.md  — 修复摘要
  knowledge/ci-failure-patterns.md        — 积累的失败模式知识库
"""

import os
import re
import base64
import requests
from datetime import datetime

GITHUB_API = "https://api.github.com"
CI_DATA_BRANCH = "ci-data"


def _repo() -> str:
    return os.environ.get('GITHUB_REPOSITORY', 'sunshuang1866/docker-images-workflow')


def _token() -> str:
    return os.environ.get('DISPATCH_TOKEN') or os.environ.get('GITHUB_TOKEN', '')


def _headers() -> dict:
    return {
        'Authorization': f'token {_token()}',
        'Accept': 'application/vnd.github.v3+json',
    }


def _ensure_branch() -> None:
    """ci-data 分支不存在时从 main 创建。"""
    url = f"{GITHUB_API}/repos/{_repo()}/git/refs/heads/{CI_DATA_BRANCH}"
    if requests.get(url, headers=_headers(), timeout=15).ok:
        return
    resp = requests.get(
        f"{GITHUB_API}/repos/{_repo()}/git/refs/heads/main",
        headers=_headers(), timeout=15,
    )
    resp.raise_for_status()
    sha = resp.json()['object']['sha']
    requests.post(
        f"{GITHUB_API}/repos/{_repo()}/git/refs",
        headers=_headers(),
        json={'ref': f'refs/heads/{CI_DATA_BRANCH}', 'sha': sha},
        timeout=15,
    ).raise_for_status()


def read_file(path: str) -> str:
    """从 ci-data 分支读取文件，不存在返回空字符串。"""
    url = f"{GITHUB_API}/repos/{_repo()}/contents/{path}"
    resp = requests.get(url, headers=_headers(), params={'ref': CI_DATA_BRANCH}, timeout=30)
    if resp.status_code == 404:
        return ''
    resp.raise_for_status()
    return base64.b64decode(resp.json()['content']).decode('utf-8')


def write_file(path: str, content: str, message: str) -> None:
    """向 ci-data 分支写入文件（自动处理创建/更新）。"""
    _ensure_branch()
    url = f"{GITHUB_API}/repos/{_repo()}/contents/{path}"

    sha = None
    resp = requests.get(url, headers=_headers(), params={'ref': CI_DATA_BRANCH}, timeout=30)
    if resp.ok:
        sha = resp.json().get('sha')

    payload: dict = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('ascii'),
        'branch': CI_DATA_BRANCH,
    }
    if sha:
        payload['sha'] = sha

    requests.put(url, headers=_headers(), json=payload, timeout=30).raise_for_status()


# ── 便捷路径 ─────────────────────────────────────────────────────────────

def analysis_path(pr_number: int) -> str:
    return f"ci-fix/{pr_number}/ci-analysis.md"


def fix_summary_path(pr_number: int) -> str:
    return f"ci-fix/{pr_number}/code-fix-summary.md"


KNOWLEDGE_PATH = "knowledge/ci-failure-patterns.md"

KNOWLEDGE_HEADER = """\
# CI 失败模式知识库

本文件由 ci-fix-team 自动维护，记录历史 CI 失败的根因与修复模式，供 AI 分析时参考。

"""


def read_knowledge() -> str:
    """读取知识库，不存在时返回空字符串。"""
    return read_file(KNOWLEDGE_PATH)


def _extract_field(text: str, field: str) -> str:
    """从 Markdown 中提取 '- field: value' 或 '**field**: value' 格式的值。"""
    for line in text.splitlines():
        if field in line and ':' in line:
            val = line.split(':', 1)[-1].strip().lstrip('*').strip()
            if val:
                return val
    return '(未知)'


def _extract_section(text: str, heading: str) -> str:
    """提取某个 ## 节的内容（前 300 字符）。"""
    lines = text.splitlines()
    capturing = False
    result = []
    for line in lines:
        if re.match(r'#+\s*' + re.escape(heading), line):
            capturing = True
            continue
        if capturing:
            if line.startswith('#'):
                break
            result.append(line)
    return '\n'.join(result).strip()[:300]


def append_pattern(pr_number: int, repo: str, analysis: str, fix_summary: str) -> None:
    """从分析报告和修复摘要中提取失败模式，追加到知识库。"""
    failure_type = _extract_field(analysis, '失败类型')
    confidence = _extract_field(analysis, '置信度')
    root_cause = _extract_section(analysis, '根因定位')
    fix_desc = _extract_section(fix_summary, '修复的问题')
    changed_files = _extract_section(fix_summary, '修改的文件')
    date = datetime.now().strftime('%Y-%m-%d')

    entry = f"""
---

## {repo} PR #{pr_number} · {date}

| 字段 | 内容 |
|------|------|
| 失败类型 | `{failure_type}` |
| 置信度 | {confidence} |

**根因**:
{root_cause}

**修复方法**:
{fix_desc}

**涉及文件**:
{changed_files}

"""

    existing = read_knowledge()
    if not existing:
        existing = KNOWLEDGE_HEADER

    write_file(
        KNOWLEDGE_PATH,
        existing + entry,
        f'knowledge: add pattern from {repo} PR #{pr_number}',
    )
