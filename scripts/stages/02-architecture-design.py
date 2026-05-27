#!/usr/bin/env python3
"""
Stage 2: 架构设计 - Python 版本

输入: 需求分析报告
输出: $HOME/tech-design-data/work/<issue>/02-architecture-design.md
副作用:
  - 评论 issue
  - state.json 更新 phase2 状态
  - 标 issue label ai-phase2
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from scripts.lib.opencode_run import run_opencode
from scripts.lib.github_api import get_issue, add_labels, remove_label
from scripts.lib.stage_common import (
    parse_env,
    agent_prompt_file,
    comment_agent_output,
    log_stage,
)
from scripts.lib.work_context import ensure_work_dir, write_state, read_file


async def main():
    """主函数"""
    env = parse_env()
    work_dir = ensure_work_dir(env['issue_number'])
    output_file = os.path.join(work_dir, '02-architecture-design.md')
    
    log_stage('phase2', f'issue={env["issue_number"]}, work_dir={work_dir}')
    
    # 获取 issue
    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )
    
    # 读取需求分析
    requirements_md = read_file(env['issue_number'], '01-requirements-analysis.md')
    if not requirements_md:
        raise RuntimeError('需求分析报告未找到，请先运行 Phase 1')
    
    # 更新状态
    write_state(env['issue_number'], {
        'stages': [
            {'name': 'phase0', 'label': '需求澄清', 'status': 'done'},
            {'name': 'phase1', 'label': '需求分析', 'status': 'done'},
            {'name': 'review1', 'label': '需求审核', 'status': 'done'},
            {'name': 'phase2', 'label': '架构设计', 'status': 'in_progress'},
            {'name': 'phase3', 'label': '架构评审', 'status': 'pending'},
            {'name': 'review2', 'label': '评审采纳', 'status': 'pending'},
            {'name': 'phase4', 'label': '最终修订', 'status': 'pending'},
        ],
    })
    
    # 更新标签
    try:
        remove_label(env['owner'], env['repo'], env['issue_number'], 'ai-phase1')
    except:
        pass
    
    try:
        add_labels(
            owner=env['owner'],
            repo=env['repo'],
            issue_number=env['issue_number'],
            labels=['ai-phase2'],
        )
    except Exception as e:
        log_stage('phase2', f'⚠ 添加标签失败(忽略): {e}')
    
    # 运行 opencode
    result = run_opencode(
        prompt_file=agent_prompt_file('architect'),
        context={
            'requirements_analysis': requirements_md,
            'issue': {
                'number': issue.get('number', env['issue_number']),
                'title': issue.get('title', ''),
            },
        },
        instruction='基于需求分析报告，产出完整的架构设计报告，必须使用 4+1 视图模型。',
        work_dir=work_dir,
        output_file=output_file,
        label='phase2',
    )
    
    # 评论 issue
    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 2: 架构设计报告\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n---',
    )
    
    # 更新状态
    write_state(env['issue_number'], {
        'phase2_output': output_file,
    })
    
    log_stage('phase2', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
