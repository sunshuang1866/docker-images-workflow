#!/usr/bin/env python3
"""
GitCode API — PR 监控 + CI 日志获取

v5 API (Gitee-compatible): PR 读写、评论
v4 API (GitLab-compatible): Pipeline / Job 日志
"""

import os
import re
import requests
from typing import Dict, List, Any, Optional

GITCODE_BASE = "https://gitcode.com"
MAX_LOG_CHARS = 50_000
MAX_DIFF_CHARS = 30_000

# 匹配 openEuler Jenkins CI URL，停止于空白或 HTML/Markdown 分隔符
_JENKINS_URL_RE = re.compile(r'https?://ci\.openeuler\.openatom\.cn/job/[^\s<>"\')\]\|]+')

# 实际构建 job 的架构标识符（openEuler CI 路径中第三段）
_BUILD_ARCH_RE = re.compile(r'/(?:x86[-_]64|aarch64|arm64|armv7l?|s390x|ppc64(?:le)?|riscv64)/')
# 编排/触发层 job（不包含实际构建日志）
_ORCHESTRATOR_RE = re.compile(r'/(?:trigger|gate|pre[-_]check)/')


def _url_score(url: str) -> tuple:
    """对 Jenkins URL 打分，分数越高越接近实际构建 job。

    维度：(是否含架构标识, 路径深度, 是否非编排层)
    openEuler CI 的 trigger/orchestrator URL 与构建 URL 深度相同，
    靠架构标识符区分（x86-64、aarch64 等）。
    """
    return (
        bool(_BUILD_ARCH_RE.search(url)),
        url.count('/job/'),
        not bool(_ORCHESTRATOR_RE.search(url)),
    )


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


def get_pr_file_names(repo: str, pr_number: int, token: str) -> List[str]:
    """返回 PR 涉及的文件路径列表（从 API 获取，不依赖本地 git history）。"""
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls/{pr_number}/files"
    resp = requests.get(url, params={'access_token': token}, timeout=30)
    resp.raise_for_status()
    files = resp.json()
    if not isinstance(files, list):
        return []
    return [f.get('filename') or f.get('new_path', '') for f in files
            if f.get('filename') or f.get('new_path')]


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

def _get_pr_comments(repo: str, pr_number: int, token: str) -> List[Dict]:
    """获取 PR 的所有评论（v5 API）。"""
    owner, name, _ = parse_repo(repo)
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls/{pr_number}/comments"
    try:
        resp = requests.get(url, params={'access_token': token, 'per_page': 100}, timeout=30)
        if resp.ok and isinstance(resp.json(), list):
            return resp.json()
    except Exception:
        pass
    return []


def _find_jenkins_url_in_comments(comments: List[Dict]) -> str:
    """从 PR 评论中提取最适合抓取构建日志的 Jenkins URL。

    openEuler CI 的结果评论里同时包含 trigger URL 和各架构 build URL，
    三者路径深度相同，靠架构标识符（x86-64、aarch64 等）区分。
    优先从失败相关评论中取，再用 _url_score 选出实际构建 job URL。
    """
    failed_urls: List[str] = []
    other_urls: List[str] = []
    for comment in reversed(comments):  # 最新评论优先
        body = comment.get('body', '')
        matches = _JENKINS_URL_RE.findall(body)
        if not matches:
            continue
        is_failure = any(k in body.lower() for k in ['fail', 'error', 'failed', '失败'])
        for raw in matches:
            url = raw.rstrip('.,;)>]')
            (failed_urls if is_failure else other_urls).append(url)

    candidates = failed_urls or other_urls
    if not candidates:
        return ''
    return max(candidates, key=_url_score)


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
            print(f"[ci-log] GET {url} → HTTP {resp.status_code}", flush=True)
            if resp.status_code == 200:
                lines = resp.text.split('\n')
                error_lines = [l for l in lines if any(
                    k in l.lower() for k in ['error', 'fail', 'exception', 'traceback', 'fatal']
                )]
                tail = lines[-300:]
                combined = error_lines[:150] + (['---'] if error_lines else []) + tail
                return '\n'.join(combined)[:MAX_LOG_CHARS]
        except Exception as e:
            print(f"[ci-log] GET {url} → exception: {e}", flush=True)
            continue
    return ''


def get_latest_failed_run(repo: str, head_sha: str, token: str,
                          pr_number: int = 0) -> Optional[Dict]:
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

    # 2. 收集 commit status 中的候选 URL
    candidate_urls: List[str] = []
    statuses = _get_commit_statuses(repo, head_sha, token)
    print(f"[ci-log] commit statuses: {len(statuses)} total", flush=True)
    failed = [s for s in statuses if s.get('state') in ('failure', 'error', 'failed')]
    for s in failed:
        print(f"[ci-log]   failed status: context={s.get('context')} target_url={s.get('target_url','')[:80]}", flush=True)
        target = s.get('target_url', '')
        if target:
            candidate_urls.append(target)

    # 3. 收集 PR 评论中的候选 URL（始终执行，与 step 2 统一打分）
    # commit status 上报的往往是 trigger/编排层 URL，评论里才有各架构的实际构建 URL
    if pr_number:
        comments = _get_pr_comments(repo, pr_number, token)
        print(f"[ci-log] PR #{pr_number} comments: {len(comments)} total", flush=True)
        jenkins_url = _find_jenkins_url_in_comments(comments)
        print(f"[ci-log] best Jenkins URL from comments: {jenkins_url or '(not found)'}", flush=True)
        if jenkins_url:
            candidate_urls.append(jenkins_url)

    if not candidate_urls:
        return None

    # 对所有候选 URL 统一打分，优先返回实际构建 job（架构标识 > 路径深度 > 非编排层）
    best_url = max(candidate_urls, key=_url_score)
    print(f"[ci-log] selected URL (score={_url_score(best_url)}): {best_url}", flush=True)
    return {'id': 0, 'name': 'jenkins', 'target_url': best_url}


def get_failed_job_logs(repo: str, pipeline_id: int, token: str,
                        target_url: str = '') -> str:
    # 外部 CI（如 Jenkins）：直接从 target_url 拉日志
    if target_url:
        log = _fetch_external_ci_log(target_url)
        if log:
            return log

    # pipeline_id == 0 说明来自外部 CI（Jenkins），无内置 Pipeline 可查
    if not pipeline_id:
        return ''

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
    url = f"{GITCODE_BASE}/api/v5/repos/{owner}/{name}/pulls/{pr_number}/comments"
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
