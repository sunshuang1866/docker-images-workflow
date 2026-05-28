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
from pathlib import Path
from typing import Optional

DATA_ROOT = os.getenv(
    'TECH_DESIGN_DATA_ROOT',
    os.path.join(os.path.expanduser('~'), 'tech-design-data')
)

WORK_ROOT = os.getenv(
    'TECH_DESIGN_WORKFLOW_TMP',
    os.path.join(DATA_ROOT, 'work')
)


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


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python work_context.py <issue_number>")
        sys.exit(1)

    issue_num = int(sys.argv[1])
    work_dir = ensure_work_dir(issue_num)
    print(f'✅ Work dir: {work_dir}')
