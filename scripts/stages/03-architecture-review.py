#!/usr/bin/env python3
"""
Stage 3: 架构评审

输入: 需求分析 + 架构设计
输出: $HOME/tech-design-data/work/<issue>/03-architecture-review.md
副作用: 评论 Issue
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
    output_file = os.path.join(work_dir, '03-architecture-review.md')

    log_stage('arch-review', f'issue={env["issue_number"]}, work_dir={work_dir}')

    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )

    requirements_md = read_file(env['issue_number'], '01-requirements-analysis.md')
    if not requirements_md:
        log_stage('arch-review', '本地文件缺失，尝试从 Issue 评论恢复 req-analysis')
        requirements_md = restore_phase_output(
            env['issue_number'], 'req-analysis',
            env['owner'], env['repo'],
        )

    architecture_md = read_file(env['issue_number'], '02-architecture-design.md')
    if not architecture_md:
        log_stage('arch-review', '本地文件缺失，尝试从 Issue 评论恢复 arch-design')
        architecture_md = restore_phase_output(
            env['issue_number'], 'arch-design',
            env['owner'], env['repo'],
        )

    if not requirements_md or not architecture_md:
        missing = []
        if not requirements_md:
            missing.append('需求分析')
        if not architecture_md:
            missing.append('架构设计')
        raise RuntimeError(f'{", ".join(missing)}未找到（本地+Issue评论均无），请先完成前序阶段')

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
        label='arch-review',
        conventions_file=get_conventions_file(),
    )

    if not os.path.exists(output_file):
        raise RuntimeError(
            f'opencode 未生成输出文件: {output_file}\n'
            f'result: {result}'
        )

    review_content = read_file(env['issue_number'], '03-architecture-review.md')
    if not review_content:
        raise RuntimeError(f'输出文件存在但读取失败: {output_file}')

    verdict = 'PASSED'
    if '<!-- review-verdict: NEEDS_ADJUSTMENT -->' in review_content:
        verdict = 'NEEDS_ADJUSTMENT'
    elif '<!-- review-verdict: FAILED -->' in review_content:
        verdict = 'FAILED'

    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## 架构评审报告 (arch-review)\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n**Verdict**: {verdict}\n\n---',
    )

    log_stage('arch-review', f'✅ done, verdict={verdict}')


if __name__ == '__main__':
    asyncio.run(main())
