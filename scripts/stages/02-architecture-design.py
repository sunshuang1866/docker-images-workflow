#!/usr/bin/env python3
"""
Stage 2: 架构设计

输入: 需求分析报告
输出: $HOME/tech-design-data/work/<issue>/02-architecture-design.md
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
from scripts.lib.work_context import ensure_work_dir, read_file


async def main():
    env = parse_env()
    work_dir = ensure_work_dir(env['issue_number'])
    output_file = os.path.join(work_dir, '02-architecture-design.md')

    log_stage('phase2', f'issue={env["issue_number"]}, work_dir={work_dir}')

    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )

    requirements_md = read_file(env['issue_number'], '01-requirements-analysis.md')
    if not requirements_md:
        raise RuntimeError('需求分析报告未找到，请先运行 Phase 1')

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
        conventions_file=get_conventions_file(),
    )

    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 2: 架构设计报告\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n---',
    )

    log_stage('phase2', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
