#!/usr/bin/env python3
"""
GitCode API — PR 监控 + CI 日志获取

v5 API (Gitee-compatible): PR 读写、评论
v4 API (GitLab-compatible): Pipeline / Job 日志
"""

import os
import requests
from typing import Dict, List, Any, Optional

GITCODE_BASE = "https://gitcode.com"
MAX_LOG_CHARS = 50_000
MAX_DIFF_CHARS = 30_000


def parse_repo(repo: str):
    """'https://gitcode.com/owner/name' 或 'owner/name' → (owner, name, 'owner%2Fname')"""
    repo = repo.rstrip('/')
    if repo.startswith(f'{GITCODE_BASE}/'):
        repo = repo[len(f'{GITCODE_BASE}/'):]
    parts = repo.split('/')
    owner, name = parts[0], parts[1]
    return owner, name, f"{owner}%2F{name}"


def _v5(token: str) -> Dict[str, str]:
    return {'Authorization': f'token {token}', 'Content-Type': 'application/json'}


def _v4(token: str) -> Dict[str, str]:
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


# ── PR 查询 ──

def fetch_prs_with_label(repo: str, label: str, token: str, max_prs: int = 50) -> List[Dict]:
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls"
    params = {'state': 'open', 'per_page': min(max_prs, 100), 'sort': 'updated',
              'direction': 'desc', 'access_token': token}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    prs = resp.json()
    if not isinstance(prs, list):
        return []
    return [pr for pr in prs if label in [l.get('name') for l in (pr.get('labels') or [])]]


def find_any_pr_by_head_branch(repo: str, head_branch: str, token: str,
                               open_only: bool = False) -> Optional[Dict]:
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls"
    branch_name = head_branch.split(':')[-1]
    states = ('open',) if open_only else ('open', 'closed', 'merged')
    for state in states:
        params = {'state': state, 'per_page': 50, 'access_token': token}
        resp = requests.get(url, params=params, timeout=30)
        if not resp.ok:
            continue
        for pr in resp.json() or []:
            ref = pr.get('head', {}).get('ref', '')
            if ref == head_branch or ref == branch_name or ref.split(':')[-1] == branch_name:
                return pr
    return None


def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls/{pr_number}/files"
    params = {'access_token': token}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    files = resp.json()
    if not isinstance(files, list):
        return ''
    parts = []
    for f in files:
        filename = f.get('filename', f.get('new_path', ''))
        patch = f.get('patch', '')
        if patch:
            parts.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
    return '\n'.join(parts)[:MAX_DIFF_CHARS]


def get_branch_commit_count(repo: str, branch: str, base_branch: str, token: str) -> int:
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/compare/{base_branch}...{branch}"
    params = {'access_token': token}
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 404:
        return 0
    resp.raise_for_status()
    data = resp.json()
    return len(data.get('commits', []))


# ── CI 日志获取（GitLab v4 Pipeline API + 外部 CI 兜底）──

def _get_commit_statuses(repo: str, sha: str, token: str) -> List[Dict]:
    """获取 commit 的外部 CI 状态（用于 Jenkins 等非 GitCode Pipeline CI）。"""
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/commits/{sha}/statuses"
    try:
        resp = requests.get(url, params={'access_token': token, 'per_page': 20}, timeout=30)
        if resp.ok and isinstance(resp.json(), list):
            return resp.json()
    except Exception:
        pass
    return []


def _fetch_external_ci_log(target_url: str) -> str:
    """从外部 CI URL（如 Jenkins）拉取控制台日志。"""
    base = target_url.rstrip('/')
    # Jenkins: /console 是 HTML，/consoleText 是纯文本
    text_url = (base[:-8] + '/consoleText') if base.endswith('/console') else (base + '/consoleText')
    for url in [text_url, base]:
        try:
            resp = requests.get(url, timeout=60, allow_redirects=True)
            if resp.status_code == 200:
                lines = resp.text.split('\n')
                error_lines = [l for l in lines if any(
                    k in l.lower() for k in ['error', 'fail', 'exception', 'traceback', 'fatal']
                )]
                tail = lines[-300:]
                combined = error_lines[:150] + (['---'] if error_lines else []) + tail
                return '\n'.join(combined)[:MAX_LOG_CHARS]
        except Exception:
            continue
    return ''


def get_latest_failed_run(repo: str, head_sha: str, token: str) -> Optional[Dict]:
    # 1. 优先查 GitCode 内置 Pipeline（GitLab v4 API）
    _, _, path_enc = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v4/projects/{path_enc}/pipelines"
    params = {'sha': head_sha, 'status': 'failed', 'per_page': 5}
    try:
        resp = requests.get(url, headers=_v4(token), params=params, timeout=30)
        if resp.status_code not in (404, 403):
            resp.raise_for_status()
            pipelines = resp.json()
            if isinstance(pipelines, list) and pipelines:
                return pipelines[0]
    except Exception:
        pass

    # 2. 兜底：查 commit status（外部 CI，如 Jenkins，通过 status API 上报）
    statuses = _get_commit_statuses(repo, head_sha, token)
    failed = [s for s in statuses if s.get('state') in ('failure', 'error', 'failed')]
    if failed:
        s = failed[0]
        return {
            'id': s.get('id', 0),
            'name': s.get('context', 'external-ci'),
            'target_url': s.get('target_url', ''),
        }
    return None


def get_failed_job_logs(repo: str, pipeline_id: int, token: str,
                        target_url: str = '') -> str:
    # 外部 CI（如 Jenkins）：直接从 target_url 拉日志
    if target_url:
        log = _fetch_external_ci_log(target_url)
        if log:
            return log

    # GitCode 内置 Pipeline：通过 GitLab v4 Jobs API 拉日志
    _, _, path_enc = parse_repo(repo)
    jobs_url = f"{GITCODE_BASE}/api/v4/projects/{path_enc}/pipelines/{pipeline_id}/jobs"
    try:
        resp = requests.get(jobs_url, headers=_v4(token), timeout=30)
        resp.raise_for_status()
        jobs = resp.json()
    except Exception as e:
        return f"[jobs fetch error: {e}]"

    if not isinstance(jobs, list):
        return '[no jobs found]'

    failed_jobs = [j for j in jobs if j.get('status') == 'failed'] or jobs[:3]
    parts = []

    for job in failed_jobs[:3]:
        job_id = job['id']
        job_name = job.get('name', str(job_id))
        log_url = f"{GITCODE_BASE}/api/v4/projects/{path_enc}/jobs/{job_id}/trace"
        try:
            log_resp = requests.get(log_url, headers=_v4(token), timeout=60)
            if log_resp.status_code == 200:
                raw = log_resp.text
                lines = raw.split('\n')
                error_lines = [l for l in lines if any(
                    k in l.lower() for k in ['error', 'fail', 'exception', 'traceback', 'fatal']
                )]
                tail = lines[-300:]
                combined = error_lines[:150] + (['---'] if error_lines else []) + tail
                content = '\n'.join(combined)[:20000]
                parts.append(f"### Job: {job_name}\n```\n{content}\n```")
            else:
                parts.append(f"### Job: {job_name}\n[HTTP {log_resp.status_code}]")
        except Exception as e:
            parts.append(f"### Job: {job_name}\n[log fetch error: {e}]")

    return '\n\n'.join(parts)[:MAX_LOG_CHARS]


# ── PR 操作 ──

def close_pull_request(repo: str, pr_number: int, token: str):
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls/{pr_number}"
    resp = requests.patch(url, params={'access_token': token}, json={'state': 'closed'}, timeout=30)
    resp.raise_for_status()


def add_pr_comment(repo: str, pr_number: int, body: str, token: str):
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/issues/{pr_number}/comments"
    resp = requests.post(url, params={'access_token': token}, json={'body': body}, timeout=30)
    resp.raise_for_status()


def create_pull_request(repo: str, head_branch: str, base_branch: str,
                        title: str, body: str, token: str) -> Dict:
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls"
    payload = {'title': title, 'body': body, 'head': head_branch, 'base': base_branch}
    resp = requests.post(url, params={'access_token': token}, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def add_label_to_pr(repo: str, pr_number: int, labels: List[str], token: str):
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/issues/{pr_number}/labels"
    resp = requests.post(url, params={'access_token': token}, json={'labels': labels}, timeout=30)
    resp.raise_for_status()
