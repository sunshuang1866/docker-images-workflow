#!/usr/bin/env python3
"""
Issue 事件流处理脚本
- 读取 watchlist.json 获取监控仓库列表
- 使用 GitHub API 查询每个仓库的新 Issue 事件
- 对触发标签的 Issue 启动 AI 分析流程
- 在 dev-workflow 仓库内完成所有操作
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 项目根目录
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)

# 配置文件路径
WATCHLIST_FILE = os.path.join(PROJECT_ROOT, 'config', 'watchlist.json')
STATE_FILE = os.path.join(PROJECT_ROOT, 'config', '.watch-state.json')


def log(msg: str):
    """日志输出"""
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def load_watchlist() -> Dict[str, Any]:
    """加载监控配置"""
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_state() -> Dict[str, Any]:
    """加载处理状态（避免重复处理）"""
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'processed_issues': {}, 'last_run': None}


def save_state(state: Dict[str, Any]):
    """保存处理状态"""
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    state['last_run'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_github_headers(token: str) -> Dict[str, str]:
    """获取 GitHub API 请求头"""
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


def fetch_recent_issues(
    repo: str,
    trigger_labels: List[str],
    since: str,
    token: str,
    max_events: int = 50
) -> List[Dict[str, Any]]:
    """
    获取仓库中带有触发标签的 Issue
    
    Args:
        repo: 仓库地址 (owner/repo)
        trigger_labels: 触发标签列表
        since: ISO 时间字符串（保留但不用于过滤）
        token: GitHub Token
        max_events: 最大事件数
    
    Returns:
        Issue 列表
    """
    log(f"📡 Fetching issues from {repo} with labels: {trigger_labels}")
    
    all_issues = []
    
    # GitHub API 的 labels 参数是 AND 关系，需要分别查询每个标签
    for label in trigger_labels:
        try:
            url = f"https://api.github.com/repos/{repo}/issues"
            params = {
                'state': 'all',
                'labels': label,  # 单个标签，OR 关系
                'per_page': min(max_events, 100),
                'sort': 'updated',
                'direction': 'desc'
            }
            
            response = requests.get(
                url,
                headers=get_github_headers(token),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            issues = response.json()
            
            log(f"  ✅ Label '{label}': Found {len(issues)} issues")
            all_issues.extend(issues)
            
        except Exception as e:
            log(f"  ❌ Failed to fetch issues with label '{label}': {e}")
    
    # 去重（同一个 issue 可能有多个触发标签）
    seen_ids = set()
    unique_issues = []
    for issue in all_issues:
        if issue['id'] not in seen_ids:
            seen_ids.add(issue['id'])
            unique_issues.append(issue)
    
    log(f"  📊 Total unique issues: {len(unique_issues)}")
    return unique_issues


def is_issue_processed(issue_id: int, repo: str, state: Dict[str, Any]) -> bool:
    """检查 Issue 是否已处理"""
    key = f"{repo}:{issue_id}"
    return key in state.get('processed_issues', {})


def mark_issue_processed(issue_id: int, repo: str, state: Dict[str, Any]):
    """标记 Issue 已处理"""
    key = f"{repo}:{issue_id}"
    state.setdefault('processed_issues', {})[key] = {
        'timestamp': datetime.now().isoformat(),
        'repo': repo,
        'issue_id': issue_id
    }


def trigger_ai_analysis(issue: Dict[str, Any], repo: str, token: str):
    """
    触发 AI 分析流程
    
    使用 GitHub API 创建 dispatch 事件到本地工作流
    或者直接在当前进程中启动分析
    """
    issue_number = issue['number']
    issue_title = issue['title']
    issue_body = issue.get('body') or ''
    
    log(f"🚀 Triggering AI analysis for #{issue_number}: {issue_title}")
    
    # 获取目标仓库（dev-workflow 仓库）
    target_repo = os.getenv('GITHUB_REPOSITORY', '')
    if not target_repo:
        # 如果在本地测试，使用默认值
        target_repo = 'ZhengZhenyu/dev-workflow'
        log(f"⚠️  GITHUB_REPOSITORY not set, using default: {target_repo}")
    
    log(f"   Target repo: {target_repo}")
    
    # 方式 1: 通过 repository_dispatch 触发本地工作流
    # 这样可以在同一个仓库内启动完整的分析流程
    dispatch_url = f"https://api.github.com/repos/{target_repo}/dispatches"
    
    payload = {
        'event_type': 'watched-issue-trigger',
        'client_payload': {
            'issue_number': issue_number,
            'issue_title': issue_title,
            'issue_body': issue_body,
            'source_repo': repo,
            'source_owner': repo.split('/')[0],
            'labels': issue.get('labels', []),
            'action': 'labeled',
            'detected_at': datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(
            dispatch_url,
            headers=get_github_headers(token),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 204:
            log(f"  ✅ Dispatch sent successfully")
            return True
        else:
            log(f"  ❌ Dispatch failed with HTTP {response.status_code}")
            log(f"     Response: {response.text}")
            return False
            
    except Exception as e:
        log(f"  ❌ Failed to send dispatch: {e}")
        return False


def process_all_repos():
    """处理所有监控仓库"""
    # 加载配置
    watchlist = load_watchlist()
    state = load_state()
    
    # 获取 Tokens
    watch_token = os.getenv('WATCH_TOKEN') or os.getenv('DISPATCH_TOKEN')
    dispatch_token = os.getenv('DISPATCH_TOKEN')
    
    if not watch_token:
        log("❌ WATCH_TOKEN or DISPATCH_TOKEN not set")
        sys.exit(1)
    
    if not dispatch_token:
        log("❌ DISPATCH_TOKEN not set")
        sys.exit(1)
    
    # 计算查询时间窗口
    lookback_minutes = watchlist.get('settings', {}).get('lookback_minutes', 10)
    since_time = (datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)).isoformat()
    
    max_events = watchlist.get('settings', {}).get('max_events_per_run', 50)
    
    # 是否测试特定仓库
    test_repo = os.getenv('TEST_REPO', '')
    
    # 是否强制重新处理所有 Issue（忽略状态文件）
    force_reprocess = os.getenv('FORCE_REPROCESS', '').lower() in ('true', '1', 'yes')
    
    if force_reprocess:
        log("⚠️  FORCE_REPROCESS enabled: will reprocess all issues")
        state['processed_issues'] = {}
    
    log(f"🔍 Starting monitoring cycle")
    log(f"   Since: {since_time}")
    log(f"   Max events per run: {max_events}")
    log(f"   GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY', 'NOT SET')}")
    log(f"   WATCH_TOKEN configured: {'Yes' if watch_token else 'No'}")
    log(f"   DISPATCH_TOKEN configured: {'Yes' if dispatch_token else 'No'}")
    if test_repo:
        log(f"   Test mode: {test_repo}")
    
    repos_to_check = watchlist.get('watched_repos', [])
    
    # 如果指定了测试仓库，只检查该仓库
    if test_repo:
        repos_to_check = [r for r in repos_to_check if r['repo'] == test_repo]
        if not repos_to_check:
            log(f"❌ Test repo {test_repo} not found in watchlist")
            sys.exit(1)
    
    triggered_count = 0
    
    for repo_config in repos_to_check:
        repo = repo_config['repo']
        trigger_labels = repo_config.get('trigger_labels', ['rfc', 'bug'])
        enabled = repo_config.get('enabled', True)
        
        if not enabled:
            log(f"⏭️  Skipping disabled repo: {repo}")
            continue
        
        log(f"\n{'='*60}")
        log(f"📦 Checking: {repo}")
        log(f"   Trigger labels: {trigger_labels}")
        
        # 获取最近的 Issue
        issues = fetch_recent_issues(
            repo=repo,
            trigger_labels=trigger_labels,
            since=since_time,
            token=watch_token,
            max_events=max_events
        )
        
        # 处理每个 Issue
        for issue in issues:
            issue_id = issue['id']
            issue_number = issue['number']
            issue_title = issue.get('title', 'Untitled')
            issue_state = issue.get('state', 'unknown')
            labels = [l['name'] for l in issue.get('labels', [])]
            
            log(f"  📋 Issue #{issue_number}: {issue_title} (state: {issue_state})")
            log(f"     Labels: {labels}")
            
            if is_issue_processed(issue_id, repo, state):
                log(f"  ⏭️  Already processed: #{issue_number}")
                continue
            
            log(f"  🚀 Triggering analysis for #{issue_number}...")
            
            # 触发 AI 分析
            success = trigger_ai_analysis(issue, repo, dispatch_token)
            
            if success:
                mark_issue_processed(issue_id, repo, state)
                triggered_count += 1
            else:
                log(f"  ⚠️  Will retry on next cycle")
    
    # 保存状态
    save_state(state)
    
    log(f"\n{'='*60}")
    log(f"✅ Monitoring cycle completed")
    log(f"   Triggered: {triggered_count} issues")
    log(f"   Processed issues in state: {len(state.get('processed_issues', {}))}")


if __name__ == '__main__':
    process_all_repos()
