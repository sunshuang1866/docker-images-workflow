#!/usr/bin/env python3
"""
GitHub API 封装 - Python 版本 (使用 requests 库)
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional

GH_TOKEN = os.getenv('GITHUB_TOKEN', '')


def get_headers() -> Dict[str, str]:
    """获取 GitHub API 请求头"""
    return {
        'Authorization': f'token {GH_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }


def get_issue(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """获取 Issue 详情"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> str:
    """添加 Issue 评论"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    response = requests.post(
        url,
        headers=get_headers(),
        json={'body': body},
        timeout=30
    )
    response.raise_for_status()
    return 'Comment added'


def update_comment(owner: str, repo: str, comment_id: int, body: str) -> str:
    """更新评论"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
    response = requests.patch(
        url,
        headers=get_headers(),
        json={'body': body},
        timeout=30
    )
    response.raise_for_status()
    return 'Comment updated'


def list_comments(owner: str, repo: str, issue_number: int, per_page: int = 30) -> List[Dict[str, Any]]:
    """列出 Issue 评论"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    response = requests.get(
        url,
        headers=get_headers(),
        params={'per_page': per_page},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def add_labels(owner: str, repo: str, issue_number: int, labels: List[str]) -> str:
    """添加标签"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.post(
        url,
        headers=get_headers(),
        json={'labels': labels},
        timeout=30
    )
    response.raise_for_status()
    return 'Labels added'


def remove_label(owner: str, repo: str, issue_number: int, label: str) -> Optional[str]:
    """移除标签"""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
        response = requests.delete(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        return 'Label removed'
    except:
        # label may not exist, ignore
        return None


def set_stage_label(owner: str, repo: str, issue_number: int, new_stage: Optional[str] = None) -> None:
    """设置 stage 标签（移除旧的，添加新的）"""
    # 移除所有旧的 stage: 标签
    labels_to_remove = [
        'stage:phase0', 'stage:phase1', 'stage:phase2',
        'stage:phase3', 'stage:phase4', 'stage:review'
    ]
    for label in labels_to_remove:
        remove_label(owner, repo, issue_number, label)
    
    # 添加新标签
    if new_stage:
        add_labels(owner, repo, issue_number, labels=[new_stage])


def get_issue_labels(owner: str, repo: str, issue_number: int) -> List[str]:
    """获取 Issue 的所有标签"""
    issue = get_issue(owner, repo, issue_number)
    return [label['name'] for label in issue.get('labels', [])]


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python github_api.py <owner> <repo> <issue_number>")
        sys.exit(1)
    
    owner, repo, issue_num = sys.argv[1], sys.argv[2], int(sys.argv[3])
    
    try:
        issue = get_issue(owner, repo, issue_num)
        print(f'✅ Issue #{issue_num}: {issue.get("title")}')
        print(f'   Labels: {", ".join(get_issue_labels(owner, repo, issue_num))}')
    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)
