#!/usr/bin/env python3
"""
Stage 1: 需求分析

输入: GitHub Issue
输出: $HOME/tech-design-data/work/<issue>/01-requirements-analysis.md
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
    output_file = os.path.join(work_dir, '01-requirements-analysis.md')

    log_stage('phase1', f'issue={env["issue_number"]}, work_dir={work_dir}')

    issue = get_issue(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
    )

    result = run_opencode(
        prompt_file=agent_prompt_file('requirement-analyst'),
        context={
            'issue': {
                'title': issue.get('title', ''),
                'body': issue.get('body') or '(no body)',
                'number': issue.get('number', env['issue_number']),
            },
        },
        instruction='基于 Issue 内容，产出完整的需求分析报告。',
        work_dir=work_dir,
        output_file=output_file,
        label='phase1',
        conventions_file=get_conventions_file(),
    )

    await comment_agent_output(
        owner=env['owner'],
        repo=env['repo'],
        issue_number=env['issue_number'],
        output_file=output_file,
        heading=f'## Phase 1: 需求分析报告\n\n**Issue**: #{env["issue_number"]} - {issue.get("title", "")}\n\n---',
    )

    log_stage('phase1', '✅ done')


if __name__ == '__main__':
    asyncio.run(main())
