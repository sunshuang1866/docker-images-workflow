#!/usr/bin/env python3
"""
tech-design-team 工作目录管理

目录布局:
  $HOME/tech-design-data/
  └── work/<issue_number>/
      ├── 01-requirements-analysis.md
      ├── 02-architecture-design.md
      ├── 03-architecture-review.md
      └── opencode-*.log
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, List

DATA_ROOT = os.getenv(
    'TECH_DESIGN_DATA_ROOT',
    os.path.join(os.path.expanduser('~'), 'tech-design-data')
)

WORK_ROOT = os.getenv(
    'TECH_DESIGN_WORKFLOW_TMP',
    os.path.join(DATA_ROOT, 'work')
)

PHASE_FILENAME_MAP = {
    'req-analysis': '01-requirements-analysis.md',
    'arch-design': '02-architecture-design.md',
    'arch-review': '03-architecture-review.md',
}

COMMENT_HEADING_MAP = {
    '01-requirements-analysis.md': '需求分析报告 (req-analysis)',
    '02-architecture-design.md': '架构设计报告 (arch-design)',
    '03-architecture-review.md': '架构评审报告 (arch-review)',
}


def get_work_dir(issue_number: int) -> str:
    return os.path.join(WORK_ROOT, str(issue_number))


def ensure_work_dir(issue_number: int) -> str:
    work_dir = get_work_dir(issue_number)
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    return work_dir


def read_file(issue_number: int, filename: str) -> Optional[str]:
    file_path = os.path.join(get_work_dir(issue_number), filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_file(issue_number: int, filename: str, content: str) -> str:
    work_dir = ensure_work_dir(issue_number)
    file_path = os.path.join(work_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def file_exists(issue_number: int, filename: str) -> bool:
    file_path = os.path.join(get_work_dir(issue_number), filename)
    return os.path.exists(file_path)


def extract_body_from_comment(comment_body: str) -> Optional[str]:
    heading_keyword = COMMENT_HEADING_MAP.get(
        _infer_filename_from_comment(comment_body), ''
    )
    if not heading_keyword:
        return None

    pattern = re.compile(
        r'^## ' + re.escape(heading_keyword) + r'\s*\n'
        r'(?:.*\n)*?'
        r'^---\s*\n'
        r'(?s:(.+))',
        re.MULTILINE,
    )
    match = pattern.search(comment_body)
    if match:
        return match.group(1).strip()

    fallback = re.compile(
        r'^## ' + re.escape(heading_keyword) + r'\s*\n(.+)',
        re.MULTILINE | re.DOTALL,
    )
    match = fallback.search(comment_body)
    if match:
        content = match.group(1).strip()
        lines = content.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if line.strip() == '---':
                body_start = i + 1
                break
        if body_start > 0 and body_start < len(lines):
            return '\n'.join(lines[body_start:]).strip()
        return content

    return None


def _infer_filename_from_comment(comment_body: str) -> Optional[str]:
    for filename, keyword in COMMENT_HEADING_MAP.items():
        if keyword in comment_body:
            return filename
    return None


def restore_from_issue(
    issue_number: int,
    filename: str,
    owner: str,
    repo: str,
    token: Optional[str] = None,
) -> Optional[str]:
    from scripts.lib.github_api import list_comments

    heading_keyword = COMMENT_HEADING_MAP.get(filename)
    if not heading_keyword:
        return None

    old_token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        os.environ['GITHUB_TOKEN'] = token

    try:
        comments: List = list_comments(owner, repo, issue_number, per_page=100)
    except Exception:
        return None
    finally:
        if token:
            os.environ['GITHUB_TOKEN'] = old_token

    for comment in reversed(comments):
        body = comment.get('body', '') or ''
        if heading_keyword not in body:
            continue

        content = extract_body_from_comment(body)
        if content:
            write_file(issue_number, filename, content)
            return content

    return None


def restore_phase_output(
    issue_number: int,
    phase: str,
    owner: str,
    repo: str,
    token: Optional[str] = None,
) -> Optional[str]:
    filename = PHASE_FILENAME_MAP.get(phase)
    if not filename:
        return None

    local = read_file(issue_number, filename)
    if local:
        return local

    return restore_from_issue(issue_number, filename, owner, repo, token)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python work_context.py <issue_number>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'restore':
        if len(sys.argv) < 5:
            print("Usage: python work_context.py restore <issue_number> <owner/repo> <phase>")
            sys.exit(1)
        issue_num = int(sys.argv[2])
        repo_full = sys.argv[3]
        phase = sys.argv[4]
        owner, repo_name = repo_full.split('/', 1)
        content = restore_phase_output(issue_num, phase, owner, repo_name)
        if content:
            print(f'✅ Restored {phase} ({len(content)} chars)')
        else:
            print(f'❌ No comment found for {phase}')
            sys.exit(1)
    else:
        issue_num = int(cmd)
        work_dir = ensure_work_dir(issue_num)
        print(f'✅ Work dir: {work_dir}')
