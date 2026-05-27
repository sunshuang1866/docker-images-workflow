#!/usr/bin/env python3
"""
Stage 3: 架构评审 - Python 版本

输入: 需求分析 + 架构设计
输出: $HOME/tech-design-data/work/<issue>/03-architecture-review.md
副作用:
  - 评论 issue
  - state.json 更新 phase3 状态
  - 标 issue label ai-phase3
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
    output_file = os.path.join(work_dir, '03-architecture-review.md')
    
    log_stage('phase3', f'issue={env["issue_number"]}, work_dir={work_dir}')
    
    # 获取 issue
    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )
    
    # 读取需求分析和架构设计
    requirements_md = read_file(env['issue_number'], '01-requirements-analysis.md')
    architecture_md = read_file(env['issue_number'], '02-architecture-design.md')
    
    if not requirements_md or not architecture_md:
        raise RuntimeError('需求分析或架构设计未找到，请先完成前序阶段')
    
    # 更新状态
    write_state(env['issue_number'], {
        'stages': [
            {'name': 'phase0', 'label': '需求澄清', 'status': 'done'},
            {'name': 'phase1', 'label': '需求分析', 'status': 'done'},
            {'name': 'review1', 'label': '需求审核', 'status': 'done'},
            {'name': 'phase2', 'label': '架构设计', 'status': 'done'},
            {'name': 'phase3', 'label': '架构评审', 'status': 'in_progress'},
            {'name': 'review2', 'label': '评审采纳', 'status': 'pending'},
            {'name': 'phase4', 'label': '最终修订', 'status': 'pending'},
        ],
    })
    
    # 更新标签
    try:
        remove_label(env['owner'], env['repo'], env['issue_number'], 'ai-phase2')
    except:
        pass
    
    try:
        add_labels(
            owner=env['owner'],
            repo=env['repo'],
            issue_number=env['issue_number'],
            labels=['ai-phase3', 'ai-review-needed'],
        )
    except Exception as e:
        log_stage('phase3', f'⚠ 添加标签失败(忽略): {e}')
    
    # 运行 opencode
    result = run_opencode(
        prompt_file=agent_prompt_file('architecture-reviewer'),
        context={
            'requirements_analysis': requirements_md,
            'architecture_design': architecture_md,
            'issue': {
                'number': issue.get('number', env['issue_number']),
                'title': issue.get('title', ''),
            },
        },
        instruction='基于需求分析和架构设计两份文档，产出完整的架构评审报告，必须包含 Verdict Marker。',
        work_dir=work_dir,
        output_file=output_file,
        label='phase3',
        conventions_file=get_conventions_file(),
    )
    
    # 读取输出并解析 Verdict
    with open(output_file, 'r', encoding='utf-8') as f:
        review_content = f.read()
    
    verdict = 'PASSED'
    if '<!-- review-verdict: NEEDS_ADJUSTMENT -->' in review_content:
        verdict = 'NEEDS_ADJUSTMENT'
    elif '<!-- review-verdict: FAILED -->' in review_content:
        verdict = 'FAILED'
    
    # 评论 issue
    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 3: 架构评审报告\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n**Verdict**: {verdict}\n\n---',
    )
    
    # 更新状态
    write_state(env['issue_number'], {
        'phase3_output': output_file,
        'phase3_verdict': verdict,
        'phase3_iterations': 0,
    })
    
    log_stage('phase3', f'✅ done (verdict: {verdict})')


if __name__ == '__main__':
    asyncio.run(main())
