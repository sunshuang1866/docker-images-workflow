#!/usr/bin/env python3
"""
Phase 0: 需求澄清 - Python 版本

输入: GitHub issue (title + body)
输出: $HOME/tech-design-data/work/<issue>/00-phase0-clarification.md
副作用:
  - 评论 issue 发布 Phase 0 提问
  - state.json 更新 phase0 状态
  - 标 issue label ai-phase0
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from scripts.lib.opencode_run import run_opencode
from scripts.lib.github_api import get_issue, add_labels
from scripts.lib.stage_common import (
    parse_env,
    agent_prompt_file,
    comment_agent_output,
    log_stage,
)
from scripts.lib.work_context import ensure_work_dir, write_state


async def main():
    """主函数"""
    env = parse_env()
    work_dir = ensure_work_dir(env['issue_number'])
    output_file = os.path.join(work_dir, '00-phase0-clarification.md')
    
    log_stage('phase0', f'issue={env["issue_number"]}, work_dir={work_dir}')
    
    # 获取 issue 详情
    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )
    
    # 更新状态
    write_state(env['issue_number'], {
        'stage': 'phase0',
        'stages': [
            {'name': 'phase0', 'label': '需求澄清', 'status': 'in_progress'},
            {'name': 'phase1', 'label': '需求分析', 'status': 'pending'},
            {'name': 'review1', 'label': '需求审核', 'status': 'pending'},
            {'name': 'phase2', 'label': '架构设计', 'status': 'pending'},
            {'name': 'phase3', 'label': '架构评审', 'status': 'pending'},
            {'name': 'review2', 'label': '评审采纳', 'status': 'pending'},
            {'name': 'phase4', 'label': '最终修订', 'status': 'pending'},
        ],
    })
    
    # 添加标签
    try:
        add_labels(
            owner=env['owner'],
            repo=env['repo'],
            issue_number=env['issue_number'],
            labels=['ai-phase0'],
        )
    except Exception as e:
        log_stage('phase0', f'⚠ 添加标签失败(忽略): {e}')
    
    # 运行 opencode
    result = run_opencode(
        prompt_file=agent_prompt_file('phase0-clarification'),
        context={
            'issue': {
                'title': issue.get('title', ''),
                'body': issue.get('body') or '(no body)',
                'number': issue.get('number', env['issue_number']),
                'user': issue.get('user', {}).get('login', ''),
            },
        },
        instruction='基于 issue 内容，输出 4 个维度的结构化提问，帮助用户澄清需求细节。',
        work_dir=work_dir,
        output_file=output_file,
        label='phase0',
    )
    
    # 评论 issue
    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 0: 需求澄清\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n请在下方回复你的答案，或使用 `/ai-answer` 命令快速回答：\n\n---',
    )
    
    # 更新状态为完成
    write_state(env['issue_number'], {
        'phase0_output': output_file,
    })
    
    log_stage('phase0', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
