#!/usr/bin/env python3
"""
tech-design-team 工作目录管理 + state.json 读写 - Python 版本

目录布局:
  $HOME/tech-design-data/
  └── work/<issue_number>/
      ├── 00-phase0-clarification.md
      ├── 01-requirements-analysis.md
      ├── 02-architecture-design.md
      ├── 03-architecture-review.md
      ├── 04-architecture-design-final.md
      ├── state.json
      └── opencode-*.log
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 路径常量
DATA_ROOT = os.getenv(
    'TECH_DESIGN_DATA_ROOT',
    os.path.join(os.path.expanduser('~'), 'tech-design-data')
)

WORK_ROOT = os.getenv(
    'TECH_DESIGN_WORKFLOW_TMP',
    os.path.join(DATA_ROOT, 'work')
)


def get_work_dir(issue_number: int) -> str:
    """获取 issue 工作目录路径"""
    return os.path.join(WORK_ROOT, str(issue_number))


def ensure_work_dir(issue_number: int) -> str:
    """确保工作目录存在并返回路径"""
    work_dir = get_work_dir(issue_number)
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    return work_dir


def read_state(issue_number: int) -> Optional[Dict[str, Any]]:
    """读取 state.json"""
    state_file = os.path.join(get_work_dir(issue_number), 'state.json')
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_state(issue_number: int, partial: Dict[str, Any]) -> Dict[str, Any]:
    """
    写入 state.json (合并更新)
    
    Args:
        issue_number: Issue 编号
        partial: 要更新的部分数据
    
    Returns:
        更新后的完整 state
    """
    work_dir = ensure_work_dir(issue_number)
    state_file = os.path.join(work_dir, 'state.json')
    
    # 读取现有 state
    current = read_state(issue_number) or {
        'issue_number': int(issue_number),
        'stages': [
            {'name': 'phase0', 'label': '需求澄清', 'status': 'pending'},
            {'name': 'phase1', 'label': '需求分析', 'status': 'pending'},
            {'name': 'review1', 'label': '需求审核', 'status': 'pending'},
            {'name': 'phase2', 'label': '架构设计', 'status': 'pending'},
            {'name': 'phase3', 'label': '架构评审', 'status': 'pending'},
            {'name': 'review2', 'label': '评审采纳', 'status': 'pending'},
            {'name': 'phase4', 'label': '最终修订', 'status': 'pending'},
        ],
    }
    
    # 合并更新
    from datetime import datetime
    next_state = {
        **current,
        **partial,
        'issue_number': int(issue_number),
        'updated_at': datetime.now().isoformat(),
    }
    
    # 写入文件
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(next_state, f, indent=2, ensure_ascii=False)
    
    return next_state


def read_file(issue_number: int, filename: str) -> Optional[str]:
    """读取工作目录中的文件"""
    file_path = os.path.join(get_work_dir(issue_number), filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_file(issue_number: int, filename: str, content: str) -> str:
    """写入文件到工作目录"""
    work_dir = ensure_work_dir(issue_number)
    file_path = os.path.join(work_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def file_exists(issue_number: int, filename: str) -> bool:
    """检查文件是否存在"""
    file_path = os.path.join(get_work_dir(issue_number), filename)
    return os.path.exists(file_path)


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python work_context.py <issue_number>")
        sys.exit(1)
    
    issue_num = int(sys.argv[1])
    
    # 测试创建工作目录
    work_dir = ensure_work_dir(issue_num)
    print(f'✅ Work dir: {work_dir}')
    
    # 测试写入 state
    state = write_state(issue_num, {'test_key': 'test_value'})
    print(f'✅ State: {json.dumps(state, indent=2, ensure_ascii=False)}')
    
    # 测试读取 state
    state2 = read_state(issue_num)
    print(f'✅ Read state: {state2 is not None}')
