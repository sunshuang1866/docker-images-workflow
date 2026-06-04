# docker-images-workflow

基于 GitHub Actions 和 AI 大模型的 **PR CI 失败自动修复**工作流。

## 功能特性

- **自动检测 CI 失败**：监控目标仓库中带有 `ci-failed` label 的 PR，每 5 分钟轮询一次
- **两阶段 AI 修复**：
  - `ci-log-analysis`：AI 分析 CI 日志，定位根因，产出结构化诊断报告
  - `code-fix`：AI 基于诊断报告在代码库中实施最小化修复并提交
- **自动提交 Fix PR**：创建 `fix/<pr-number>` 分支并发起 Fix PR
- **智能重试**：Fix PR CI 再次失败时自动追加新 commit 继续修复，无需创建新 PR
- **超限关闭**：超过最大重试次数（默认 3 次）自动关闭 Fix PR，通知人工介入
- **跨仓库监控**：源仓库无需任何配置，由 docker-images-workflow 集中驱动所有修复
- **多平台支持**：同时兼容 GitHub 和 GitCode 仓库，自动识别平台，无需手动切换

## 工作流程

```
目标仓库 PR 获得 ci-failed label
  ↓
Monitor 每5min轮询，检测 ci-failed PR
  ↓
ci-log-analysis: AI 分析 CI 日志 + PR diff → 诊断报告
  ↓（自动推进）
code-fix: AI 修改代码 → git commit → push fix/<pr-number>
  ↓
自动创建 Fix PR（如尚不存在）
  ↓
Fix PR CI 通过 ────────────────→ 完成 ✅
Fix PR CI 失败（次数 < 3）→ 重新进入 ci-log-analysis
Fix PR CI 失败（次数 ≥ 3）→ 关闭 Fix PR，通知人工介入 ⚠️
```

每次重试都是独立的全新分析，直接读取当前代码库状态和最新 CI 日志，不依赖历史上下文。

## 项目结构

```
.
├── .github/
│   ├── agents/
│   │   ├── ci-failure-analyst.md   # AI Agent 1: CI 失败诊断师
│   │   └── code-fixer.md           # AI Agent 2: 代码修复工程师
│   └── workflows/
│       ├── stream-pr-events.yml    # PR 监控（每5分钟 cron）
│       └── pr-ci-fix-trigger.yml   # CI 修复执行链路（两阶段）
├── config/
│   └── watchlist.json              # 监控仓库列表配置
├── scripts/
│   ├── lib/
│   │   ├── ai_runner.py            # AI Agent 统一入口（按 AI_RUNNER 分发）
│   │   ├── opencode_run.py         # AI 调用封装 — OpenCode 后端
│   │   ├── claude_code_run.py      # AI 调用封装 — Claude Code 后端
│   │   ├── ci_api.py               # 平台工厂（detect / normalize / get_api）
│   │   ├── ci_github_api.py        # GitHub API 封装（PR、CI 日志）
│   │   ├── ci_gitcode_api.py       # GitCode API 封装（v5 PR + v4 Pipeline）
│   │   ├── stage_common.py         # 阶段脚本公共工具
│   │   └── discover_conventions.py # 自动读取源仓库项目规范
│   ├── stages/
│   │   ├── ci-log-analysis.py      # 阶段1: CI 日志分析脚本
│   │   └── code-fix.py             # 阶段2: 代码修复脚本
│   └── watch/
│       └── process_pr_events.py    # PR 轮询 + dispatch 决策逻辑
└── requirements.txt
```

## 配置

### 1. 监控仓库列表

编辑 `config/watchlist.json`，添加需要监控的仓库：

```json
{
  "watched_repos": [
    {
      "repo": "owner/repo-name",
      "trigger_labels": ["ci-failed"],
      "enabled": true,
      "description": "GitHub 仓库示例（owner/repo 格式）"
    },
    {
      "repo": "https://gitcode.com/owner/repo-name",
      "trigger_labels": ["ci-failed"],
      "enabled": true,
      "description": "GitCode 仓库示例（完整 URL 格式，自动识别平台）"
    }
  ],
  "settings": {
    "poll_interval_minutes": 5,
    "max_events_per_run": 50
  }
}
```

平台识别规则：URL 中包含 `gitcode.com` 则使用 GitCode API，否则使用 GitHub API。

### 2. GitHub Secrets

在 docker-images-workflow 仓库 **Settings → Secrets and variables → Actions** 中配置：

| Secret | 用途 | 所需权限 |
|--------|------|---------|
| `OPENAI_API_KEY` | OpenCode 模型 API Key（`AI_RUNNER=opencode`） | — |
| `ANTHROPIC_API_KEY` | Anthropic API Key（`AI_RUNNER=claude-code`） | — |
| `CLAUDE_CREDENTIALS_JSON` | Claude.ai 账号 OAuth 凭证（`AI_RUNNER=claude-code-account`） | — |
| `WATCH_TOKEN` | 读取 GitHub 目标仓库 PR / CI 日志 | `contents:read`, `actions:read` |
| `DISPATCH_TOKEN` | 触发 repository_dispatch（GitHub） | `repo`, `workflow` |
| `WRITE_TOKEN` | 向 GitHub 目标仓库推送代码 + 创建 PR | `contents:write`, `pull-requests:write` |
| `GITCODE_WATCH_TOKEN` | 读取 GitCode 仓库 PR / CI 日志 | GitCode Personal Access Token |
| `GITCODE_WRITE_TOKEN` | 向 GitCode 仓库推送代码 + 创建 PR | GitCode Personal Access Token（需 push 权限）|

### 3. GitHub Variables（可选）

**通用**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_RUNNER` | AI 后端选择：`opencode` / `claude-code` / `claude-code-account` | `opencode` |

**OpenCode（`AI_RUNNER=opencode`）**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_MODEL` | 模型名称 | `alibaba-cn/glm-5.1` |
| `AI_AGENT` | Agent 类型 | `build` |
| `AI_EXTRA_ARGS` | 额外参数 | `--dangerously-skip-permissions` |
| `OPENCODE_TIMEOUT_MS` | 单次调用超时（毫秒） | `600000` |
| `OPENAI_BASE_URL` | 自定义 API 地址（兼容 OpenAI 接口） | 使用默认 |

**Claude Code（`AI_RUNNER=claude-code`）**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CLAUDE_MODEL` | 模型名称 | `claude-sonnet-4-6` |
| `CLAUDE_EXTRA_ARGS` | 额外参数 | `--dangerously-skip-permissions` |
| `CLAUDE_TIMEOUT_MS` | 单次调用超时（毫秒） | `600000` |

## 前置条件：目标仓库需打 `ci-failed` label

目标仓库的 CI 需在失败时自动为 PR 打 `ci-failed` label。

**GitHub 仓库示例**：

```yaml
# .github/workflows/ci.yml（目标仓库，片段）
- name: Add ci-failed label on failure
  if: failure()
  uses: actions-ecosystem/action-add-labels@v1
  with:
    labels: ci-failed
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

**GitCode 仓库示例**（GitLab CI）：

```yaml
# .gitlab-ci.yml（目标仓库，片段）
label-ci-failed:
  stage: .post
  script:
    - |
      curl -X POST "https://gitcode.com/api/v5/repos/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/issues/${CI_MERGE_REQUEST_IID}/labels" \
        -H "Content-Type: application/json" \
        -d '{"labels": "ci-failed"}' \
        -H "Authorization: token ${GITCODE_TOKEN}"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_failure
```

## 技术栈

- **GitHub Actions**：工作流编排 + cron 调度
- **Python 3.11**：阶段脚本 + 工具库
- **OpenCode / Claude Code**：AI 模型调用（可切换，见下方配置）
- **GitHub API**：GitHub 仓库 PR 读写、Actions CI 日志获取、评论
- **GitCode API**：GitCode 仓库 PR 读写（Gitee-compatible v5）、Pipeline 日志获取（GitLab v4）

## AI 后端配置

### 使用 OpenCode（默认）

OpenCode 兼容 OpenAI 接口，支持阿里通义、GLM 等国内模型。

**Secrets**：将 API Key 填入 `OPENAI_API_KEY`

| 提供商 | 获取地址 | `AI_MODEL` 示例 |
|--------|---------|----------------|
| 阿里通义 | https://bailian.console.aliyun.com/ | `alibaba-cn/qwen-plus` |
| 智谱 AI | https://open.bigmodel.cn/ | `alibaba-cn/glm-5.1` |
| OpenAI | https://platform.openai.com/api-keys | `openai/gpt-4o` |

### 使用 Claude Code（API Key 模式）

Claude Code 使用 Anthropic 原生 API，无需兼容层。

**切换方式**：将 Variable `AI_RUNNER` 设为 `claude-code`

**Secrets**：将 Anthropic API Key 填入 `ANTHROPIC_API_KEY`

| `CLAUDE_MODEL` 示例 | 说明 |
|--------------------|------|
| `claude-sonnet-4-6` | 推荐，速度与质量均衡（默认） |
| `claude-opus-4-8` | 最强推理，适合复杂修复场景 |
| `claude-haiku-4-5-20251001` | 最快，适合简单 lint / 格式修复 |

> **提示**：获取 Anthropic API Key 请访问 https://console.anthropic.com/settings/keys

### 使用 Claude Code（账号模式，无需 API Key）

适合已有 Claude Pro / Max 订阅的用户，使用 OAuth 凭证而非 API Key，不产生额外 API 费用。

**切换方式**：将 Variable `AI_RUNNER` 设为 `claude-code-account`

**获取凭证（一次性操作，在本地机器执行）**：

```bash
# 1. 在本机登录 Claude Code
claude

# 首次运行时会引导完成 OAuth 登录（浏览器跳转）
# 登录成功后凭证保存在 ~/.claude/.credentials.json

# 2. 查看凭证内容，复制备用
cat ~/.claude/.credentials.json
```

**配置 GitHub Secret**：

将上述 `~/.claude/.credentials.json` 的完整 JSON 内容存入仓库 Secret `CLAUDE_CREDENTIALS_JSON`。

> ⚠️ **注意**：OAuth Token 会过期（通常数周至数月），过期后需重新在本机登录并更新 Secret。
> `CLAUDE_MODEL` / `CLAUDE_EXTRA_ARGS` / `CLAUDE_TIMEOUT_MS` 变量与 API Key 模式相同。

## GitCode Token 获取

`GITCODE_WATCH_TOKEN` 和 `GITCODE_WRITE_TOKEN` 均为 GitCode Personal Access Token：

1. 登录 [gitcode.com](https://gitcode.com)
2. 进入 **个人设置 → Access Tokens**
3. 创建两个 Token（或复用同一个）：

| Token | 所需 Scope |
|-------|-----------|
| `GITCODE_WATCH_TOKEN` | `read_repository`、`read_api` |
| `GITCODE_WRITE_TOKEN` | `read_repository`、`write_repository`、`read_api`、`write_api` |
