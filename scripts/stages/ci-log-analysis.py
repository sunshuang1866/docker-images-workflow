#!/usr/bin/env python3
"""
Stage 1: CI 日志分析

输入: PR 信息 + CI 失败日志
输出: $HOME/tech-design-data/ci-fix/<pr_number>/ci-analysis.md
副作用: 评论 PR，dispatch code-fix 阶段
"""

import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from scripts.lib.ai_runner import run_agent
from scripts.lib.stage_common import agent_prompt_file, log_stage, get_conventions_file
from scripts.lib.ci_github_api import (
    get_pr_diff,
    get_latest_failed_run,
    get_failed_job_logs,
    add_pr_comment,
)

WORK_BASE = os.path.join(Path.home(), 'tech-design-data', 'ci-fix')


def parse_env() -> dict:
    source_repo = os.getenv('SOURCE_REPO', '')
    pr_number = int(os.getenv('PR_NUMBER', '0'))
    if not source_repo or not pr_number:
        raise ValueError('SOURCE_REPO and PR_NUMBER are required')
    owner, repo = source_repo.split('/', 1)
    return {
        'source_repo': source_repo,
        'owner': owner,
        'repo': repo,
        'pr_number': pr_number,
        'pr_title': os.getenv('PR_TITLE', ''),
        'head_sha': os.getenv('HEAD_SHA', ''),
        'fix_branch': os.getenv('FIX_BRANCH', f'fix/{pr_number}'),
        'pr_base_branch': os.getenv('PR_BASE_BRANCH', 'main'),
        'token': os.getenv('GITHUB_TOKEN', ''),
        'dispatch_token': os.getenv('GITHUB_TOKEN', ''),
    }


def dispatch_code_fix(env: dict, analysis: str):
    target_repo = os.getenv('GITHUB_REPOSITORY', 'sunshuang1866/docker-images-workflow')
    payload = {
        'event_type': 'run-ci-fix-phase',
        'client_payload': {
            'phase': 'code-fix',
            'source_repo': env['source_repo'],
            'pr_number': env['pr_number'],
            'pr_title': env['pr_title'],
            'pr_head_sha': env['head_sha'],
            'fix_branch': env['fix_branch'],
            'pr_base_branch': env['pr_base_branch'],
            'analysis': analysis[:8000],
        }
    }
    url = f"https://api.github.com/repos/{target_repo}/dispatches"
    headers = {
        'Authorization': f"token {env['dispatch_token']}",
        'Accept': 'application/vnd.github.v3+json',
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code == 204:
        log_stage('ci-log-analysis', f'✅ Dispatched code-fix for PR #{env["pr_number"]}')
    else:
        raise RuntimeError(f'Dispatch code-fix failed HTTP {resp.status_code}: {resp.text}')


def main():
    env = parse_env()
    work_dir = os.path.join(WORK_BASE, str(env['pr_number']))
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    output_file = os.path.join(work_dir, 'ci-analysis.md')

    log_stage('ci-log-analysis', f"repo={env['source_repo']} pr=#{env['pr_number']}")

    # 获取 PR diff
    log_stage('ci-log-analysis', 'fetching PR diff...')
    pr_diff = ''
    try:
        pr_diff = get_pr_diff(env['source_repo'], env['pr_number'], env['token'])
        log_stage('ci-log-analysis', f'PR diff: {len(pr_diff)} chars')
    except Exception as e:
        log_stage('ci-log-analysis', f'⚠️ PR diff fetch failed: {e}')

    # 获取 CI 失败日志
    log_stage('ci-log-analysis', f"fetching CI logs for sha={env['head_sha'][:8]}...")
    ci_logs = ''
    run_info = ''
    try:
        run = get_latest_failed_run(env['source_repo'], env['head_sha'], env['token'])
        if run:
            run_info = f"Workflow: {run.get('name', '')}, run_id={run['id']}"
            log_stage('ci-log-analysis', f'Found failed run: {run_info}')
            ci_logs = get_failed_job_logs(env['source_repo'], run['id'], env['token'])
            log_stage('ci-log-analysis', f'CI logs: {len(ci_logs)} chars')
        else:
            log_stage('ci-log-analysis', '⚠️ No failed workflow run found for this SHA')
    except Exception as e:
        log_stage('ci-log-analysis', f'⚠️ CI log fetch failed: {e}')

    context = {
        'pr': {
            'number': env['pr_number'],
            'title': env['pr_title'],
            'diff': pr_diff or '(not available)',
        },
        'ci': {
            'run_info': run_info or '(not available)',
            'logs': ci_logs or '(not available — analyze based on PR diff only)',
        },
    }

    run_agent(
        prompt_file=agent_prompt_file('ci-failure-analyst'),
        context=context,
        instruction='根据 CI 日志和 PR diff，产出完整的 CI 失败分析报告。',
        work_dir=work_dir,
        output_file=output_file,
        label='ci-log-analysis',
        conventions_file=get_conventions_file(),
    )

    with open(output_file, 'r', encoding='utf-8') as f:
        analysis = f.read()

    # 评论到原始 PR
    heading = (
        f"## 🔍 CI 失败分析 (ci-log-analysis)\n\n"
        f"**PR**: #{env['pr_number']} — {env['pr_title']}\n\n---"
    )
    try:
        add_pr_comment(
            env['source_repo'], env['pr_number'],
            f"{heading}\n\n{analysis}",
            env['token'],
        )
    except Exception as e:
        log_stage('ci-log-analysis', f'⚠️ PR comment failed: {e}')

    # 自动推进到 code-fix 阶段
    dispatch_code_fix(env, analysis)
    log_stage('ci-log-analysis', '✅ done')


if __name__ == '__main__':
    main()
