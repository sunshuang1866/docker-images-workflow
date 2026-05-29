#!/usr/bin/env python3
"""
Stage 2: 架构设计

输入: 需求分析报告 + (可选) 架构评审反馈
输出: $HOME/tech-design-data/work/<issue>/02-architecture-design.md
副作用: 评论 Issue

当存在前一轮 arch-review 产出时，将其作为 review_feedback 传入 context，
使 architect agent 针对评审意见进行修订而非从头重做。
"""

import os
import sys
import asyncio
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from scripts.lib.opencode_run import run_opencode
from scripts.lib.github_api import get_issue
from scripts.lib.stage_common import (
    parse_env,
    agent_prompt_file,
    comment_agent_output,
    log_stage,
    get_conventions_file,
)
from scripts.lib.work_context import ensure_work_dir, read_file, restore_phase_output


async def main():
    env = parse_env()
    work_dir = ensure_work_dir(env['issue_number'])
    output_file = os.path.join(work_dir, '02-architecture-design.md')

    log_stage('arch-design', f'issue={env["issue_number"]}, work_dir={work_dir}')

    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )

    requirements_md = read_file(env['issue_number'], '01-requirements-analysis.md')
    if not requirements_md:
        log_stage('arch-design', '本地文件缺失，尝试从 Issue 评论恢复 req-analysis')
        requirements_md = restore_phase_output(
            env['issue_number'], 'req-analysis',
            env['owner'], env['repo'],
        )
    if not requirements_md:
        raise RuntimeError('需求分析报告未找到（本地+Issue评论均无），请先运行 req-analysis')

    review_md = read_file(env['issue_number'], '03-architecture-review.md')
    if not review_md:
        log_stage('arch-design', '本地文件缺失，尝试从 Issue 评论恢复 arch-review')
        review_md = restore_phase_output(
            env['issue_number'], 'arch-review',
            env['owner'], env['repo'],
        )

    context = {
        'requirements_analysis': requirements_md,
        'issue': {
            'number': issue.get('number', env['issue_number']),
            'title': issue.get('title', ''),
        },
    }

    if review_md:
        log_stage('arch-design', f'包含评审反馈 ({len(review_md)} chars)，将针对评审意见修订')
        context['review_feedback'] = review_md
        instruction = '基于需求分析报告，针对架构评审的反馈意见修订架构设计。必须逐条回应 Blocking 问题，保留原有合理设计，仅修改评审指出的缺陷部分。仍然使用 4+1 视图模型。'
    else:
        instruction = '基于需求分析报告，产出完整的架构设计报告，必须使用 4+1 视图模型。'

    result = run_opencode(
        prompt_file=agent_prompt_file('architect'),
        context=context,
        instruction=instruction,
        work_dir=work_dir,
        output_file=output_file,
        label='arch-design',
        conventions_file=get_conventions_file(),
    )

    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## 架构设计报告 (arch-design)\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n---',
    )

    log_stage('arch-design', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
