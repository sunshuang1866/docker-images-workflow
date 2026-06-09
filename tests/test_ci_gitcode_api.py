"""
Tests for scripts/lib/ci_gitcode_api.py

覆盖范围：
- _url_score: Jenkins URL 打分逻辑
- _find_jenkins_url_in_comments: 从 PR 评论中选取最优构建 URL
- get_latest_failed_run: 候选 URL 收集与择优（mock HTTP）
"""

import pytest
from unittest.mock import patch, MagicMock

from scripts.lib.ci_gitcode_api import (
    _url_score,
    _find_jenkins_url_in_comments,
    get_latest_failed_run,
)

# ── 共享测试 URL 常量 ──────────────────────────────────────────────────────────

TRIGGER  = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/trigger/job/openeuler-docker-images/1396/console'
X86      = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/x86-64/job/openeuler-docker-images/1391/console'
AARCH64  = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/aarch64/job/openeuler-docker-images/1366/console'
ARM64    = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/arm64/job/openeuler-docker-images/100/console'
S390X    = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/s390x/job/openeuler-docker-images/200/console'
GATE     = 'https://ci.openeuler.openatom.cn/job/multiarch/job/openeuler/job/gate/job/openeuler-docker-images/300/console'
SHALLOW  = 'https://ci.openeuler.openatom.cn/job/check/123/console'


# ── _url_score ────────────────────────────────────────────────────────────────

class TestUrlScore:
    def test_trigger_scores_lowest(self):
        assert _url_score(TRIGGER) == (False, 4, False)

    def test_x86_build_scores_highest(self):
        assert _url_score(X86) == (True, 4, True)

    def test_aarch64_scores_same_as_x86(self):
        assert _url_score(AARCH64) == _url_score(X86)

    def test_arm64_detected_as_build(self):
        is_build, _, _ = _url_score(ARM64)
        assert is_build is True

    def test_s390x_detected_as_build(self):
        is_build, _, _ = _url_score(S390X)
        assert is_build is True

    def test_gate_is_orchestrator(self):
        is_build, _, not_orch = _url_score(GATE)
        assert is_build is False
        assert not_orch is False

    def test_depth_counted_correctly(self):
        _, depth, _ = _url_score(X86)
        assert depth == 4

    def test_shallow_url_has_lower_depth(self):
        _, shallow_depth, _ = _url_score(SHALLOW)
        _, deep_depth, _ = _url_score(X86)
        assert shallow_depth < deep_depth

    def test_build_beats_trigger_with_same_depth(self):
        assert _url_score(X86) > _url_score(TRIGGER)

    def test_deeper_non_arch_beats_shallower(self):
        # 同为非架构 URL，深的优先
        assert _url_score(TRIGGER) > _url_score(SHALLOW)


# ── _find_jenkins_url_in_comments ─────────────────────────────────────────────

def _comment(body: str) -> dict:
    return {'body': body}


class TestFindJenkinsUrlInComments:
    def test_empty_comments(self):
        assert _find_jenkins_url_in_comments([]) == ''

    def test_no_jenkins_url(self):
        assert _find_jenkins_url_in_comments([_comment('nothing here')]) == ''

    def test_single_trigger_url_returned_as_fallback(self):
        comments = [_comment(f'门禁运行中 {TRIGGER}')]
        assert _find_jenkins_url_in_comments(comments) == TRIGGER

    def test_build_url_beats_trigger_in_same_failure_comment(self):
        # 真实 PR #2534 场景：一条评论含 trigger + x86 + aarch64，且有 FAILED 关键词
        body = (
            f'<table>x86_64 FAILED {X86}\n'
            f'aarch64 FAILED {AARCH64}\n'
            f'trigger {TRIGGER}</table>'
        )
        result = _find_jenkins_url_in_comments([_comment(body)])
        assert result in (X86, AARCH64)  # 任一构建 URL 均可
        assert 'trigger' not in result

    def test_failure_comment_beats_neutral_comment(self):
        # 失败评论里的 trigger URL 也比非失败评论里的 trigger URL 优先
        # 但如果失败评论里只有 trigger，仍返回 trigger
        comments = [
            _comment(f'CI 运行中 {TRIGGER}'),        # neutral
            _comment(f'build FAILED {X86}'),          # failure，有 build URL
        ]
        result = _find_jenkins_url_in_comments(comments)
        assert result == X86

    def test_all_urls_from_all_comments_are_considered(self):
        # build URL 在不同评论里，应被收集到
        comments = [
            _comment(f'check FAILED {TRIGGER}'),
            _comment(f'downstream build failed {X86}'),
        ]
        result = _find_jenkins_url_in_comments(comments)
        assert result == X86

    def test_url_trailing_punctuation_stripped(self):
        body = f'see {X86}.'
        result = _find_jenkins_url_in_comments([_comment(body)])
        assert result == X86

    def test_multiple_arch_urls_returns_one_of_them(self):
        body = f'x86 failed {X86} aarch64 failed {AARCH64} failed'
        result = _find_jenkins_url_in_comments([_comment(body)])
        assert result in (X86, AARCH64)

    def test_prefers_failure_keyword_comment_over_neutral(self):
        comments = [
            _comment(f'passed {X86}'),       # neutral with build URL
            _comment(f'error {TRIGGER}'),    # failure with trigger URL
        ]
        # failure 评论的 trigger 分数 (False,4,False) < neutral 的 build URL (True,4,True)
        result = _find_jenkins_url_in_comments(comments)
        # failure 组有 TRIGGER，neutral 组有 X86；failure 优先选 → 结果是 TRIGGER
        assert result == TRIGGER

    def test_chinese_failure_keyword(self):
        body = f'构建失败 {X86}'
        result = _find_jenkins_url_in_comments([_comment(body)])
        assert result == X86

    def test_real_pr2534_comment_structure(self):
        # 完整还原 PR #2534 的两条评论
        comment_running = _comment(
            f'门禁正在运行，查看实时结果:\n{TRIGGER}'
        )
        comment_table = _comment(
            f'<table>\n'
            f'check_sca SUCCESS {TRIGGER}\n'
            f'x86_64 check_build FAILED {X86}\n'
            f'aarch64 check_build FAILED {AARCH64}\n'
            f'</table>'
        )
        result = _find_jenkins_url_in_comments([comment_running, comment_table])
        assert result in (X86, AARCH64)
        assert 'trigger' not in result


# ── get_latest_failed_run ─────────────────────────────────────────────────────

REPO  = 'openeuler/openeuler-docker-images'
SHA   = 'abc123def456'
TOKEN = 'test-token'


def _mock_pipeline_404():
    """GitCode 内置 pipeline API 返回 404（openEuler 用 Jenkins，无内置 pipeline）。"""
    m = MagicMock()
    m.status_code = 404
    return m


class TestGetLatestFailedRun:
    def _patch(self, pipeline_resp=None, statuses=None, comments=None):
        """返回三个 patch 的 context manager 元组。"""
        if pipeline_resp is None:
            pipeline_resp = _mock_pipeline_404()
        return (
            patch('scripts.lib.ci_gitcode_api.requests.get', return_value=pipeline_resp),
            patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses or []),
            patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=comments or []),
        )

    def test_returns_none_when_nothing_found(self):
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=[]), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=1)
        assert result is None

    def test_gitcode_pipeline_returned_directly(self):
        pipeline = MagicMock()
        pipeline.status_code = 200
        pipeline.json.return_value = [{'id': 99, 'status': 'failed'}]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=pipeline), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=[]), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN)
        assert result == {'id': 99, 'status': 'failed'}

    def test_build_url_from_comments_beats_trigger_from_status(self):
        # commit status → trigger URL；评论 → x86 build URL；应选 build URL
        statuses  = [{'state': 'failure', 'context': 'ci', 'target_url': TRIGGER}]
        comments  = [_comment(f'x86_64 FAILED {X86}')]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=comments):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=42)
        assert result is not None
        assert result['target_url'] == X86

    def test_arch_build_url_from_status_kept_when_no_better_in_comments(self):
        # commit status 直接上报了 x86 build URL，评论里没有更好的
        statuses = [{'state': 'failure', 'context': 'build', 'target_url': X86}]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=42)
        assert result['target_url'] == X86

    def test_trigger_returned_when_only_candidate(self):
        # 没有任何 build URL，只有 trigger，fallback 返回 trigger
        statuses = [{'state': 'failure', 'context': 'ci', 'target_url': TRIGGER}]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=42)
        assert result['target_url'] == TRIGGER

    def test_comments_only_no_status(self):
        # commit status 空，全靠评论
        comments = [_comment(f'aarch64 build failed {AARCH64}')]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=[]), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=comments):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=10)
        assert result['target_url'] == AARCH64

    def test_no_pr_number_skips_comments(self):
        # pr_number=0，跳过评论步骤，只用 commit status
        statuses = [{'state': 'failure', 'target_url': TRIGGER}]
        mock_get_comments = MagicMock()
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments', mock_get_comments):
            get_latest_failed_run(REPO, SHA, TOKEN, pr_number=0)
        mock_get_comments.assert_not_called()

    def test_pipeline_exception_falls_through(self):
        # pipeline API 抛异常，应继续走 commit status + 评论
        statuses = [{'state': 'failed', 'target_url': X86}]
        with patch('scripts.lib.ci_gitcode_api.requests.get', side_effect=Exception('timeout')), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=5)
        assert result['target_url'] == X86

    def test_status_without_target_url_ignored(self):
        # state=failure 但无 target_url，不应加入候选
        statuses = [{'state': 'failure', 'context': 'ci', 'target_url': ''}]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=0)
        assert result is None

    def test_multiple_arch_builds_in_status_best_scored_wins(self):
        # 两条 status，一条 trigger 一条 x86，选 x86
        statuses = [
            {'state': 'failure', 'target_url': TRIGGER},
            {'state': 'failure', 'target_url': X86},
        ]
        with patch('scripts.lib.ci_gitcode_api.requests.get', return_value=_mock_pipeline_404()), \
             patch('scripts.lib.ci_gitcode_api._get_commit_statuses', return_value=statuses), \
             patch('scripts.lib.ci_gitcode_api._get_pr_comments',     return_value=[]):
            result = get_latest_failed_run(REPO, SHA, TOKEN, pr_number=0)
        assert result['target_url'] == X86
