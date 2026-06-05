#!/usr/bin/env python3
"""
Stage 2: 代码修复

输入: CI 分析报告 + 源代码仓库（已 checkout 到 fix 分支）
输出: 源代码修改（git commit）+ 修复摘要文件
副作用: 评论 PR
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from scripts.lib.ai_runner import run_agent
from scripts.lib.stage_common import agent_prompt_file, log_stage, get_conventions_file
from scripts.lib.ci_api import get_api

WORK_BASE = os.path.join(Path.home(), 'tech-design-data', 'ci-fix')
SOURCE_REPO_DIR = os.path.join(PROJECT_ROOT, 'source-repo')


def parse_env() -> dict:
    source_repo = os.getenv('SOURCE_REPO', '')
    pr_number = int(os.getenv('PR_NUMBER', '0'))
    if not source_repo or not pr_number:
        raise ValueError('SOURCE_REPO and PR_NUMBER are required')
    owner, repo = source_repo.split('/', 1)
    platform = os.getenv('SOURCE_PLATFORM', 'github')
    token = os.getenv('GITHUB_TOKEN', '')
    if platform == 'gitcode':
        token = os.getenv('GITCODE_WRITE_TOKEN') or token
    return {
        'source_repo': source_repo,
        'source_platform': platform,
        'owner': owner,
        'repo': repo,
        'pr_number': pr_number,
        'pr_title': os.getenv('PR_TITLE', ''),
        'pr_head_sha': os.getenv('PR_HEAD_SHA', ''),
        'fix_branch': os.getenv('FIX_BRANCH', f'fix/{pr_number}'),
        'pr_base_branch': os.getenv('PR_BASE_BRANCH', 'main'),
        'analysis': os.getenv('ANALYSIS', ''),
        'token': token,
    }


def git(args: list, cwd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['git'] + args, cwd=cwd, check=check,
                          capture_output=True, text=True)


def has_changes(cwd: str) -> bool:
    result = git(['diff', '--cached', '--quiet'], cwd=cwd, check=False)
    return result.returncode != 0


def get_pr_file_list(cwd: str, pr_head_sha: str, base_branch: str) -> list:
    """返回原始 PR diff 中涉及的文件列表。"""
    result = git(
        ['diff', '--name-only', f'origin/{base_branch}...{pr_head_sha}'],
        cwd=cwd, check=False
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]


AI_ARTIFACT_DIRS = {'.claude', '.opencode', '__pycache__', '.aider'}
AI_ARTIFACT_SUFFIXES = {'.pyc', '.pyo'}


def _cleanup_ai_artifacts(repo_dir: str):
    root = Path(repo_dir)
    for name in AI_ARTIFACT_DIRS:
        for p in root.rglob(name):
            if p.is_dir():
                shutil.rmtree(p)
                log_stage('code-fix', f'removed dir: {p.relative_to(root)}')
            elif p.is_file():
                p.unlink()
                log_stage('code-fix', f'removed file: {p.relative_to(root)}')
    for suffix in AI_ARTIFACT_SUFFIXES:
        for p in root.rglob(f'*{suffix}'):
            p.unlink()
            log_stage('code-fix', f'removed file: {p.relative_to(root)}')


def main():
    env = parse_env()
    work_dir = os.path.join(WORK_BASE, str(env['pr_number']))
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    # 摘要文件写在 work_dir（源码库之外），不会被 git commit 进去
    output_file = os.path.join(work_dir, 'code-fix-summary.md')

    log_stage('code-fix', f"repo={env['source_repo']} [{env['source_platform']}] pr=#{env['pr_number']}")

    if not env['analysis']:
        raise RuntimeError('ANALYSIS env var is empty — ci-log-analysis must run first')

    if not os.path.isdir(SOURCE_REPO_DIR):
        raise RuntimeError(f'source-repo directory not found: {SOURCE_REPO_DIR}')

    pr_files = get_pr_file_list(SOURCE_REPO_DIR, env['pr_head_sha'], env['pr_base_branch'])
    log_stage('code-fix', f'PR touched {len(pr_files)} file(s): {pr_files}')

    context = {
        'pr': {
            'number': env['pr_number'],
            'title': env['pr_title'],
            'changed_files': pr_files,
        },
        'ci_analysis': env['analysis'],
        'fix_branch': env['fix_branch'],
    }

    # AI Agent 在源码仓库目录中运行，直接读写源文件
    run_agent(
        prompt_file=agent_prompt_file('code-fixer'),
        context=context,
        instruction=(
            '根据 CI 失败分析报告，对源代码进行最小化修复。'
            f'只允许修改以下文件（原始 PR 涉及的文件）：{pr_files}。'
            '修复完成后，将修复摘要写入 output_file（不要写入源码仓库内部）。'
        ),
        work_dir=SOURCE_REPO_DIR,
        output_file=output_file,
        label='code-fix',
        conventions_file=get_conventions_file(),
    )

    # 清理 AI 工具产生的文件，不应提交到源码仓库
    _cleanup_ai_artifacts(SOURCE_REPO_DIR)

    # 只暂存原始 PR 涉及的文件，严禁提交无关文件
    log_stage('code-fix', 'staging changes (PR files only)...')
    if pr_files:
        for f in pr_files:
            git(['add', '--', f], cwd=SOURCE_REPO_DIR, check=False)
    else:
        log_stage('code-fix', '⚠️ PR file list empty, falling back to git add -A')
        git(['add', '-A'], cwd=SOURCE_REPO_DIR)

    if not has_changes(SOURCE_REPO_DIR):
        raise RuntimeError('code-fixer made no changes — cannot commit empty diff')

    with open(output_file, 'r', encoding='utf-8') as f:
        summary = f.read().strip()

    first_line = summary.split('\n')[0].lstrip('#').strip()[:72]
    commit_msg = (
        f"fix(ci): {first_line}\n\n"
        f"Automated fix for CI failure in PR #{env['pr_number']}\n\n"
        f"🤖 Generated by ci-fix-team"
    )

    git(['commit', '-m', commit_msg], cwd=SOURCE_REPO_DIR)
    log_stage('code-fix', '✅ committed')

    # 评论到原始 PR
    comment_body = (
        f"## 🔧 代码修复完成 (code-fix)\n\n"
        f"**PR**: #{env['pr_number']} — {env['pr_title']}\n"
        f"**Fix branch**: `{env['fix_branch']}`\n\n---\n\n"
        f"{summary}"
    )
    try:
        api = get_api(env['source_platform'])
        api.add_pr_comment(env['source_repo'], env['pr_number'], comment_body, env['token'])
    except Exception as e:
        log_stage('code-fix', f'⚠️ PR comment failed: {e}')

    log_stage('code-fix', '✅ done')


if __name__ == '__main__':
    main()
