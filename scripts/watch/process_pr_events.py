#!/usr/bin/env python3
"""
PR 监控 — CI 失败自动修复触发器

轮询 watchlist 中的仓库，检测带有 ci-failed label 的 PR，
根据 fix/<pr-number> PR 的存在状态决定动作：

  fix PR 不存在           → dispatch ci-log-analysis（首次修复）
  fix PR open + ci-failed → 检查 commit 次数，未超限则 dispatch，超限则关闭 fix PR
  fix PR open             → CI 运行中，跳过
  fix PR closed/merged    → 已完成或放弃，跳过
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from scripts.lib.ci_api import detect_platform, normalize_repo, get_api

WATCHLIST_FILE = os.path.join(PROJECT_ROOT, 'config', 'watchlist.json')
CI_FAILED_LABEL = 'ci-failed'
MAX_RETRIES = 3


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def dispatch_ci_fix(repo: str, platform: str, pr: Dict, pr_base_branch: str,
                    token: str, target_repo: str) -> bool:
    payload = {
        'event_type': 'run-ci-fix-phase',
        'client_payload': {
            'phase': 'ci-log-analysis',
            'source_repo': repo,
            'source_platform': platform,
            'pr_number': pr['number'],
            'pr_title': pr.get('title', ''),
            'head_sha': pr['head']['sha'],
            'fix_branch': f"fix/{pr['number']}",
            'pr_base_branch': pr_base_branch,
        }
    }
    url = f"https://api.github.com/repos/{target_repo}/dispatches"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 204:
            log(f"  ✅ Dispatched ci-log-analysis for PR #{pr['number']}")
            return True
        log(f"  ❌ Dispatch failed HTTP {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        log(f"  ❌ Dispatch error: {e}")
        return False


def process_all():
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        watchlist = json.load(f)

    watch_token = os.getenv('WATCH_TOKEN') or os.getenv('DISPATCH_TOKEN', '')
    dispatch_token = os.getenv('DISPATCH_TOKEN') or watch_token
    target_repo = os.getenv('GITHUB_REPOSITORY', 'sunshuang1866/docker-images-workflow')

    if not watch_token:
        log("❌ WATCH_TOKEN not set")
        sys.exit(1)

    log("🔍 Starting PR monitoring cycle")
    log(f"   target_repo: {target_repo}")

    for repo_config in watchlist.get('watched_repos', []):
        if not repo_config.get('enabled', True):
            continue

        raw_repo = repo_config['repo']
        platform = detect_platform(raw_repo)
        repo = normalize_repo(raw_repo, platform)
        api = get_api(platform)

        # GitCode token 优先用 GITCODE_WATCH_TOKEN，fallback WATCH_TOKEN
        token = watch_token
        if platform == 'gitcode':
            token = os.getenv('GITCODE_WATCH_TOKEN') or watch_token

        log(f"\n{'='*60}")
        log(f"📦 {repo} [{platform}]")

        try:
            prs = api.fetch_prs_with_label(repo, CI_FAILED_LABEL, token)
        except Exception as e:
            log(f"  ❌ Failed to fetch PRs: {e}")
            continue

        log(f"  Found {len(prs)} PR(s) with '{CI_FAILED_LABEL}' label")

        for pr in prs:
            pr_number = pr['number']
            pr_base = pr['base']['ref']
            fix_branch = f'fix/{pr_number}'

            log(f"\n  🔎 PR #{pr_number}: {pr.get('title', '')[:60]}")

            fix_pr = api.find_any_pr_by_head_branch(repo, fix_branch, token)

            if fix_pr is None:
                log(f"    → No fix PR, dispatching first attempt")
                dispatch_ci_fix(repo, platform, pr, pr_base, dispatch_token, target_repo)

            elif fix_pr['state'] == 'open':
                fix_labels = [l['name'] for l in fix_pr.get('labels', [])]
                if CI_FAILED_LABEL in fix_labels:
                    count = api.get_branch_commit_count(repo, fix_branch, pr_base, token)
                    log(f"    → Fix PR #{fix_pr['number']} ci-failed, commits={count}")
                    if count >= MAX_RETRIES:
                        log(f"    → Max retries ({MAX_RETRIES}) reached, closing fix PR")
                        api.close_pull_request(repo, fix_pr['number'], token)
                        api.add_pr_comment(
                            repo, fix_pr['number'],
                            f"🤖 AI 已尝试修复 {MAX_RETRIES} 次，仍未通过 CI，自动关闭。请人工处理。",
                            token,
                        )
                        api.add_pr_comment(
                            repo, pr_number,
                            f"🤖 AI 修复 PR #{fix_pr['number']} 已尝试 {MAX_RETRIES} 次失败，已关闭，请人工介入。",
                            token,
                        )
                    else:
                        log(f"    → Dispatching retry (attempt #{count + 1})")
                        retry_pr = {
                            'number': pr_number,
                            'title': pr.get('title', ''),
                            'head': fix_pr['head'],
                        }
                        dispatch_ci_fix(repo, platform, retry_pr, pr_base, dispatch_token, target_repo)
                else:
                    log(f"    → Fix PR #{fix_pr['number']} CI running or pending, skipping")

            else:
                log(f"    → Fix PR #{fix_pr['number']} state={fix_pr['state']}, skipping")

    log(f"\n✅ PR monitoring cycle complete.")


if __name__ == '__main__':
    process_all()
