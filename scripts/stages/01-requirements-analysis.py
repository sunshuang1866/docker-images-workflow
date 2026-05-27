#!/usr/bin/env python3
"""
Stage 1: 需求分析 - Python 版本

输入: GitHub issue + Phase 0 回答
输出: $HOME/tech-design-data/work/<issue>/01-requirements-analysis.md
副作用:
  - 评论 issue
  - state.json 更新 phase1 状态
  - 标 issue label ai-phase1
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
    get_conventions_file,
)
from scripts.lib.work_context import ensure_work_dir, write_state, read_file


async def main():
    """主函数"""
    env = parse_env()
    work_dir = ensure_work_dir(env['issue_number'])
    output_file = os.path.join(work_dir, '01-requirements-analysis.md')
    
    log_stage('phase1', f'issue={env["issue_number"]}, work_dir={work_dir}')
    
    # 获取 issue
    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )
    
    # 读取 Phase 0 输出（如果有）
    phase0_answers = read_file(env['issue_number'], '00-phase0-clarification.md')
    if not phase0_answers:
        log_stage('phase1', '⚠ Phase 0 输出未找到，使用默认值')
    
    # 更新状态
    write_state(env['issue_number'], {
        'stages': [
            {'name': 'phase0', 'label': '需求澄清', 'status': 'done'},
            {'name': 'phase1', 'label': '需求分析', 'status': 'in_progress'},
            {'name': 'review1', 'label': '需求审核', 'status': 'pending'},
            {'name': 'phase2', 'label': '架构设计', 'status': 'pending'},
            {'name': 'phase3', 'label': '架构评审', 'status': 'pending'},
            {'name': 'review2', 'label': '评审采纳', 'status': 'pending'},
            {'name': 'phase4', 'label': '最终修订', 'status': 'pending'},
        ],
    })
    
    # 更新标签
    try:
        remove_label(env['owner'], env['repo'], env['issue_number'], 'ai-phase0')
    except:
        pass
    
    try:
        add_labels(
            owner=env['owner'],
            repo=env['repo'],
            issue_number=env['issue_number'],
            labels=['ai-phase1'],
        )
    except Exception as e:
        log_stage('phase1', f'⚠ 添加标签失败(忽略): {e}')
    
    # 运行 opencode
    result = run_opencode(
        prompt_file=agent_prompt_file('requirement-analyst'),
        context={
            'issue': {
                'title': issue.get('title', ''),
                'body': issue.get('body') or '(no body)',
                'number': issue.get('number', env['issue_number']),
            },
            'phase0_answers': phase0_answers,
        },
        instruction='基于 issue 内容和 Phase 0 收集的信息（如果有），产出完整的需求分析报告。',
        work_dir=work_dir,
        output_file=output_file,
        label='phase1',
        conventions_file=get_conventions_file(),
    )
    
    # 评论 issue
    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 1: 需求分析报告\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n---',
    )
    
    # 更新状态
    write_state(env['issue_number'], {
        'phase1_output': output_file,
    })
    
    log_stage('phase1', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
