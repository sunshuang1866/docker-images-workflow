#!/usr/bin/env python3
"""
GitHub API 封装 - Python 版本 (使用 GitHub CLI)
"""

import os
import json
import subprocess
from typing import List, Dict, Any, Optional

GH_TOKEN = os.getenv('GITHUB_TOKEN', '')


def run_gh(cmd: str) -> str:
    """运行 gh 命令并返回 stdout"""
    env = os.environ.copy()
    if GH_TOKEN:
        env['GH_TOKEN'] = GH_TOKEN
    
    result = subprocess.run(
        f'gh {cmd}',
        shell=True,
        capture_output=True,
        text=True,
        env=env,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f'gh command failed: {result.stderr}')
    
    return result.stdout.strip()


def run_gh_json(cmd: str) -> Any:
    """运行 gh 命令并解析 JSON 输出"""
    output = run_gh(cmd)
    return json.loads(output)


def get_issue(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """获取 Issue 详情"""
    cmd = f'issue view {issue_number} --repo {owner}/{repo} --json title,body,number,user,labels'
    return run_gh_json(cmd)


def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> str:
    """添加 Issue 评论"""
    # 使用 stdin 传递 body，避免 shell 转义问题
    env = os.environ.copy()
    if GH_TOKEN:
        env['GH_TOKEN'] = GH_TOKEN
    
    result = subprocess.run(
        f'gh issue comment {issue_number} --repo {owner}/{repo}',
        shell=True,
        input=body,
        capture_output=True,
        text=True,
        env=env,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f'Failed to add comment: {result.stderr}')
    
    return result.stdout.strip()


def update_comment(owner: str, repo: str, comment_id: int, body: str) -> str:
    """更新评论"""
    cmd = f'api repos/{owner}/{repo}/issues/comments/{comment_id} --method PATCH --field body={json.dumps(body)}'
    return run_gh(cmd)


def list_comments(owner: str, repo: str, issue_number: int, per_page: int = 30) -> List[Dict[str, Any]]:
    """列出 Issue 评论"""
    cmd = f'api repos/{owner}/{repo}/issues/{issue_number}/comments --field per_page={per_page}'
    return run_gh_json(cmd)


def add_labels(owner: str, repo: str, issue_number: int, labels: List[str]) -> str:
    """添加标签"""
    labels_str = ','.join(labels)
    cmd = f'issue edit {issue_number} --repo {owner}/{repo} --add-label "{labels_str}"'
    return run_gh(cmd)


def remove_label(owner: str, repo: str, issue_number: int, label: str) -> Optional[str]:
    """移除标签"""
    try:
        cmd = f'issue edit {issue_number} --repo {owner}/{repo} --remove-label "{label}"'
        return run_gh(cmd)
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
