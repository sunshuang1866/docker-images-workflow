#!/usr/bin/env python3
"""
stage 脚本通用配置 + 工具 - Python 版本
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 项目根目录
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)


def get_project_root() -> str:
    """获取项目根目录"""
    return PROJECT_ROOT


def agent_prompt_file(name: str) -> str:
    """获取 agent prompt 文件路径"""
    return os.path.join(PROJECT_ROOT, '.github', 'agents', f'{name}.md')


def parse_env() -> Dict[str, Any]:
    """
    从 GitHub Actions env 解析公共参数
    
    Returns:
        包含 issueNumber, owner, repo 等的字典
    """
    issue_number = int(os.getenv('ISSUE_NUMBER', '0'))
    if not issue_number:
        raise ValueError('env ISSUE_NUMBER required')
    
    github_repo = os.getenv('GITHUB_REPOSITORY', '')
    if '/' not in github_repo:
        raise ValueError('env GITHUB_REPOSITORY required')
    
    owner, repo = github_repo.split('/', 1)
    
    return {
        'issue_number': issue_number,
        'owner': owner,
        'repo': repo,
        'issue_title': os.getenv('ISSUE_TITLE', ''),
        'issue_body': os.getenv('ISSUE_BODY', ''),
    }


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Stage script')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    return parser.parse_args()


async def comment_agent_output(
    owner: str,
    repo: str,
    issue_number: int,
    output_file: str,
    heading: Optional[str] = None,
) -> str:
    """
    把 agent 输出作为评论发到本仓 issue
    
    Args:
        owner: 仓库 owner
        repo: 仓库名
        issue_number: Issue 编号
        output_file: 输出文件路径
        heading: 可选的标题
    
    Returns:
        评论内容
    """
    from .github_api import add_issue_comment
    
    with open(output_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    body = f'{heading}\n\n{md_content}' if heading else md_content
    
    return add_issue_comment(owner, repo, issue_number, body)


def ts_now() -> str:
    """获取当前时间戳 ISO 格式"""
    return datetime.now().isoformat()


def log_stage(name: str, msg: str) -> None:
    """记录 stage 日志"""
    ts = ts_now()[11:19]
    print(f'[{ts}] stage:{name} {msg}', file=sys.stderr)


async def publish_progress_board(
    owner: str,
    repo: str,
    issue_number: int,
    state: Dict[str, Any],
    issue_title: str,
) -> None:
    """
    发布进度板到 issue 评论
    
    Args:
        owner: 仓库 owner
        repo: 仓库名
        issue_number: Issue 编号
        state: state.json 内容
        issue_title: Issue 标题
    """
    from .github_api import list_comments, update_comment, add_issue_comment
    
    stages = state.get('stages', [])
    icon_map = {
        'pending': '⬜',
        'in_progress': '🔄',
        'done': '✅',
        'failed': '❌',
    }
    
    board = f'## 🤖 tech-design-team · 分析进度\n\n'
    board += f'**Issue**: #{issue_number} - {issue_title}\n\n'
    board += f'### 📊 分析进度\n\n'
    board += f'| 阶段 | 状态 |\n|------|------|\n'
    
    for stage in stages:
        icon = icon_map.get(stage['status'], '⬜')
        board += f'| {stage["label"]} ({stage["name"]}) | {icon} {stage["status"]} |\n'
    
    board += f'\n### 🔧 控制命令\n\n'
    board += f'| 命令 | 用途 |\n|------|------|\n'
    board += f'| `/accept` | 从头开始完整分析 |\n'
    board += f'| `/retry` | 从上次中断处续跑 |\n'
    board += f'| `/retry-design` | 重跑架构设计 |\n'
    board += f'| `/retry-review` | 重跑架构评审 |\n'
    board += f'| `/skip-review` | 跳过评审，接受当前设计 |\n'
    
    board += f'\n---\n<sub>🤖 tech-design-team · {ts_now()}</sub>'
    
    # 查找并更新已有的进度板评论
    try:
        comments = list_comments(owner, repo, issue_number, per_page=30)
        existing = None
        for comment in comments:
            if 'tech-design-team · 分析进度' in (comment.get('body') or ''):
                existing = comment
                break
        
        if existing:
            update_comment(owner, repo, existing['id'], board)
        else:
            add_issue_comment(owner, repo, issue_number, board)
    except Exception as e:
        # fallback: create new comment
        add_issue_comment(owner, repo, issue_number, board)


if __name__ == '__main__':
    # 测试代码
    env = parse_env()
    print(f'✅ Parsed env: {env}')
    print(f'✅ Project root: {get_project_root()}')
    print(f'✅ Agent prompt file: {agent_prompt_file("requirement-analyst")}')
