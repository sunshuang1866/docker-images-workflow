# docker-images-workflow

基于 GitHub Actions 和 AI 大模型的 **PR CI 失败自动修复**工作流。

## 功能特性

- **自动检测 CI 失败**：监控目标仓库中带有 `ci_failed` label 的 PR，轮询间隔由 `watchlist.json` 的 `poll_interval_minutes` 控制
- **仅处理正式版本**：预发布版本（`-alpha`、`-beta`、`-rc`、`-preview`、`-dev`、`-snapshot`、`-nightly` 等）的升级 PR 自动跳过，不触发修复流程；只有正式版本才会进入 AI 修复链路
- **两阶段 AI 修复**：
  - `ci-log-analysis`：AI 分析 CI 日志，定位根因，产出结构化诊断报告
  - `code-fix`：AI 基于诊断报告在代码库中实施最小化修复并提交
- **知识积累**：每次修复后自动更新 `docs/ci-failure-patterns.md`（main 分支）；新案例归入已有模式章节，若是全新失败类型则新建章节，下次分析自动参考
- **自动提交 Fix PR**：创建 `fix/<pr-number>` 分支并向上游仓库发起 Fix PR（支持 fork 模式）
- **智能重试**：Fix PR CI 再次失败时自动追加新 commit 继续修复，无需创建新 PR
- **超限关闭**：超过最大重试次数（默认 3 次）自动关闭 Fix PR，通知人工介入
- **CI 通过通知**：Fix PR 获得 `ci_successful` label 后自动在原始 PR 评论，告知 reviewer 可以合并
- **多平台支持**：同时兼容 GitHub 和 GitCode 仓库，自动识别平台

## 工作流程

```
目标仓库 PR 获得 ci_failed label
  ↓
Monitor 定时轮询，检测 ci_failed PR
  ↓
PR 标题含预发布标记？(alpha/beta/rc/preview/dev/snapshot/nightly)
  ├─ 是 → 跳过，不触发修复 🚫
  └─ 否（正式版本）↓
ci-log-analysis: AI 分析 CI 日志 + PR diff → 诊断报告（存入 ci-data 分支）
  ↓（repository_dispatch 自动推进）
code-fix: AI 修改代码 → git commit → push fix/<pr-number> 到 fork
  ↓
自动创建 Fix PR（从 fork 到上游，如尚不存在）
  ↓
Fix PR CI 通过 (ci_successful) ──→ 评论原始 PR，通知 review 合并 ✅
Fix PR CI 运行中 (ci_processing) → 等待，下次轮询再判断
Fix PR CI 失败 (ci_failed)，次数 < 3 → 重新进入 ci-log-analysis
Fix PR CI 失败 (ci_failed)，次数 ≥ 3 → 关闭 Fix PR，通知人工介入 ⚠️
```

## 项目结构

```
.
├── .github/
│   ├── agents/
│   │   ├── ci-failure-analyst.md   # AI Agent 1: CI 失败诊断师
│   │   └── code-fixer.md           # AI Agent 2: 代码修复工程师
│   └── workflows/
│       ├── stream-pr-events.yml    # PR 监控（cron，间隔由 watchlist 控制）
│       ├── pr-ci-fix-trigger.yml   # CI 修复执行链路（两阶段）
│       └── sync-poll-interval.yml  # watchlist 变更时自动同步 cron 表达式
├── config/
│   └── watchlist.json              # 监控仓库列表与轮询配置
├── docs/
│   └── ci-failure-patterns.md     # 按失败模式分类的知识库（自动维护）
├── scripts/
│   ├── lib/
│   │   ├── ai_runner.py            # AI Agent 统一入口（按 AI_RUNNER 分发）
│   │   ├── opencode_run.py         # AI 调用封装 — OpenCode 后端
│   │   ├── claude_code_run.py      # AI 调用封装 — Claude Code 后端
│   │   ├── ci_api.py               # 平台工厂（detect / normalize / get_api）
│   │   ├── ci_github_api.py        # GitHub API 封装
│   │   ├── ci_gitcode_api.py       # GitCode API 封装（v5 PR + v4 Pipeline）
│   │   ├── ci_data.py              # 分支读写：ci-fix-log（per-PR）+ main（知识库）
│   │   ├── stage_common.py         # 阶段脚本公共工具
│   │   └── discover_conventions.py # 自动读取源仓库项目规范
│   ├── stages/
│   │   ├── ci-log-analysis.py      # 阶段1: CI 日志分析
│   │   └── code-fix.py             # 阶段2: 代码修复
│   └── watch/
│       ├── process_pr_events.py    # PR 轮询 + dispatch 决策逻辑
│       └── sync_poll_interval.py   # 同步 watchlist → cron 表达式
└── requirements.txt
```

## 配置

### 1. 监控仓库列表

编辑 `config/watchlist.json`：

```json
{
  "watched_repos": [
    {
      "repo": "https://gitcode.com/owner/repo-name",
      "trigger_labels": ["ci_failed"],
      "enabled": true,
      "description": "GitCode 仓库示例"
    },
    {
      "repo": "owner/repo-name",
      "trigger_labels": ["ci_failed"],
      "enabled": true,
      "description": "GitHub 仓库示例（owner/repo 格式）"
    }
  ],
  "settings": {
    "poll_interval_minutes": 5,
    "max_events_per_run": 50,
    "lookback_minutes": 60
  }
}
```

**修改 `poll_interval_minutes` 会自动触发 `sync-poll-interval.yml`，将 cron 表达式同步到 `stream-pr-events.yml`，无需手动修改 workflow 文件。**

平台识别：URL 中含 `gitcode.com` 使用 GitCode API，否则使用 GitHub API。

### 2. GitHub Secrets

在 **Settings → Secrets and variables → Actions → Secrets** 中配置：

| Secret | 用途 | 说明 |
|--------|------|------|
| `DISPATCH_TOKEN` | 所有 GitHub 操作：触发 dispatch、ci-data 读写、checkout、推送代码、创建 PR | GitHub PAT，需 `repo` + `workflow` scope |
| `GITCODE_TOKEN` | 读写 GitCode 仓库：克隆代码、读 PR/CI 日志、推送 fork、创建 PR、评论 | GitCode PAT，需 `read_repository`、`write_repository`、`read_api`、`write_api` |
| `AI_API_KEY` | AI 模型 API Key（`AI_RUNNER=opencode` 时必填） | 填入所用模型提供商的 API Key，如 DeepSeek、通义等 |
| `CLAUDE_CREDENTIALS_JSON` | Claude.ai OAuth 凭证（`AI_RUNNER=claude-code-account` 时必填） | 见下方说明 |

### 3. GitHub Variables

在 **Settings → Secrets and variables → Actions → Variables** 中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_RUNNER` | AI 后端：`opencode` / `claude-code-account` | `opencode` |
| `AI_MODEL` | 模型名称（opencode 时如 `deepseek/deepseek-v4-pro`；claude 时如 `claude-sonnet-4-6`） | `deepseek/deepseek-v4-pro` |
| `GITCODE_FORK_REPO` | GitCode fork 仓库路径（如 `yourname/repo`），为空时直接推送原仓库 | `''` |
| `GIT_COMMIT_NAME` | Fix commit 的 git user.name（CLA 合规时必填） | `github-actions[bot]` |
| `GIT_COMMIT_EMAIL` | Fix commit 的 git user.email（CLA 合规时必填） | `github-actions[bot]@users.noreply.github.com` |

## AI 后端配置

### 使用 OpenCode（默认）

OpenCode 兼容 OpenAI 接口，支持 DeepSeek、通义等模型。

| 提供商 | `AI_MODEL` 示例 |
|--------|----------------|
| DeepSeek | `deepseek/deepseek-v4-pro` |
| 阿里通义 | `alibaba-cn/qwen-plus` |
| OpenAI | `openai/gpt-4o` |

### 使用 Claude Code（账号模式，无需 API Key）

适合已有 Claude Pro / Max 订阅的用户。

**切换方式**：将 Variable `AI_RUNNER` 设为 `claude-code-account`，`AI_MODEL` 设为对应 Claude 模型名。

**一次性获取凭证**：

```bash
# 在本地登录 Claude Code（会引导浏览器 OAuth）
claude

# 查看凭证，复制全部内容
cat ~/.claude/.credentials.json
```

将 `~/.claude/.credentials.json` 的完整 JSON 内容存入 Secret `CLAUDE_CREDENTIALS_JSON`。

> ⚠️ OAuth Token 会过期（通常数周至数月），过期后需重新登录并更新 Secret。

| `AI_MODEL` 示例 | 说明 |
|----------------|------|
| `claude-sonnet-4-6` | 推荐，速度与质量均衡（默认） |
| `claude-opus-4-8` | 最强推理，适合复杂修复场景 |
| `claude-haiku-4-5-20251001` | 最快，适合简单 lint / 格式修复 |

## GitCode Token 获取

1. 登录 [gitcode.com](https://gitcode.com)
2. **个人设置 → Access Tokens** → 创建 Token

| Token | 所需 Scope |
|-------|-----------|
| `GITCODE_TOKEN` | `read_repository`、`write_repository`、`read_api`、`write_api` |

## 前置条件：目标仓库 CI label 约定

目标仓库的 CI 需在以下时机为 PR 打对应 label：

| label | 时机 |
|-------|------|
| `ci_failed` | CI 失败时打上 |
| `ci_processing` | CI 运行中时打上 |
| `ci_successful` | CI 通过时打上 |

**GitCode（GitLab CI）示例**：

```yaml
# .gitlab-ci.yml（目标仓库，片段）
label-ci-failed:
  stage: .post
  script:
    - |
      curl -X POST "https://gitcode.com/api/v5/repos/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/issues/${CI_MERGE_REQUEST_IID}/labels" \
        -H "Content-Type: application/json" \
        -d '{"labels": ["ci_failed"]}' \
        -H "Authorization: token ${GITCODE_TOKEN}"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_failure
```

**GitHub 仓库示例**：

```yaml
# .github/workflows/ci.yml（目标仓库，片段）
- name: Add ci_failed label on failure
  if: failure()
  uses: actions-ecosystem/action-add-labels@v1
  with:
    labels: ci_failed
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## 技术栈

- **GitHub Actions**：工作流编排 + cron 调度
- **Python 3.11**：阶段脚本 + 工具库
- **OpenCode / Claude Code**：AI 模型调用（可切换）
- **GitHub Contents API**：ci-fix-log 分支（per-PR 分析报告）+ main 分支（失败模式知识库）读写
- **GitCode API v5**：PR 读写、评论、标签（Gitee-compatible）
- **GitCode API v4**：Pipeline / Job 日志获取（GitLab-compatible）
