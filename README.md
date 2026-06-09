# docker-images-workflow

基于 GitHub Actions 和 AI 大模型的 **PR CI 失败自动修复**工作流 —— 监控目标仓库中 CI 失败的升级 PR，自动分析日志、定位根因、提交修复代码并发起 Fix PR。

当前已支持 GitCode 和 GitHub 仓库，本文示例统一使用 **openeuler/openeuler-docker-images**，可扩展至任意配置了 `ci_failed` label 约定的仓库。

## 目录

- [系统架构](#系统架构)
- [前置准备](#前置准备)
- [配置监控仓库](#配置监控仓库)
- [工作流程详解](#工作流程详解)
- [AI 后端配置](#ai-后端配置)
- [CI Label 约定](#ci-label-约定)
- [跳过规则](#跳过规则)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [开发说明](#开发说明)

## 系统架构

本系统是一个由 GitHub Actions 编排的 **两阶段 AI 修复流水线**，以定时轮询作为触发入口。

```
目标仓库 PR 获得 ci_failed label
         ↓
┌────────────────────┐
│  Monitor（定时轮询）  │  stream-pr-events.yml（cron，间隔由 watchlist 控制）
│  检测 ci_failed PR   │  跳过：预发布版本 / fix: 前缀 PR
└────────┬───────────┘
         │ repository_dispatch
         ↓
┌────────────────────┐
│  ci-log-analysis   │  AI Agent 1：拉取 Jenkins 构建日志 + PR diff
│  CI 失败诊断         │  → 结构化诊断报告（存入 ci-fix-log 分支）
└────────┬───────────┘
         │ repository_dispatch
         ↓
┌────────────────────┐
│  code-fix          │  AI Agent 2：基于诊断报告在源码中实施最小化修复
│  代码修复            │  → git commit → push fix/<pr-number> → 创建 Fix PR
└────────┬───────────┘
         │
    ┌────┴───────────────────────────────────────┐
    │ Fix PR CI 结果                              │
    ├─ ci_successful ──────────────────────────→ 评论原始 PR，通知 review 合并 ✅
    ├─ ci_processing ──────────────────────────→ 等待，下次轮询再判断
    ├─ ci_failed（次数 < 3）─────────────────→ 重新进入 ci-log-analysis 循环
    └─ ci_failed（次数 ≥ 3）─────────────────→ 关闭 Fix PR，通知人工介入 ⚠️
```

运行模式一览：

| 阶段 | 触发方式 | 说明 |
|------|----------|------|
| **Monitor 轮询** | cron 定时 | 扫描 ci_failed PR，决策是否 dispatch |
| **ci-log-analysis** | repository_dispatch | AI 分析 Jenkins 日志，输出诊断报告 |
| **code-fix** | repository_dispatch | AI 修改代码，提交 Fix PR |

---

## 前置准备

### 1. GitHub Secrets

在 **Settings → Secrets and variables → Actions → Secrets** 中配置：

| Secret | 用途 | 说明 |
|--------|------|------|
| `DISPATCH_TOKEN` | 所有 GitHub 操作：触发 dispatch、ci-data 读写、checkout、推送代码、创建 PR | GitHub PAT，需 `repo` + `workflow` scope |
| `GITCODE_TOKEN` | 读写 GitCode 仓库：克隆代码、读 PR/CI 日志、推送 fork、创建 PR、评论 | GitCode PAT，需 `read_repository`、`write_repository`、`read_api`、`write_api` |
| `AI_API_KEY` | AI 模型 API Key（`AI_RUNNER=opencode` 时必填） | 填入所用模型提供商的 API Key，如 DeepSeek、通义等 |
| `CLAUDE_CREDENTIALS_JSON` | Claude.ai OAuth 凭证（`AI_RUNNER=claude-code-account` 时必填） | 见 [AI 后端配置](#ai-后端配置) |

### 2. GitHub Variables

在 **Settings → Secrets and variables → Actions → Variables** 中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_RUNNER` | AI 后端：`opencode` / `claude-code-account` | `opencode` |
| `AI_MODEL` | 模型名称（opencode 时如 `deepseek/deepseek-v4-pro`；claude 时如 `claude-sonnet-4-6`） | `deepseek/deepseek-v4-pro` |
| `GITCODE_FORK_REPO` | GitCode fork 仓库路径（如 `yourname/repo`），为空时直接推送原仓库 | `''` |
| `GIT_COMMIT_NAME` | Fix commit 的 git user.name（CLA 合规时必填） | `github-actions[bot]` |
| `GIT_COMMIT_EMAIL` | Fix commit 的 git user.email（CLA 合规时必填） | `github-actions[bot]@users.noreply.github.com` |

### 3. GitCode Token 获取

1. 登录 [gitcode.com](https://gitcode.com)
2. **个人设置 → Access Tokens** → 创建 Token

| Token | 所需 Scope |
|-------|-----------|
| `GITCODE_TOKEN` | `read_repository`、`write_repository`、`read_api`、`write_api` |

---

## 配置监控仓库

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

---

## 工作流程详解

### Monitor 轮询

`stream-pr-events.yml` 按 `poll_interval_minutes` 定时运行，对每条 `ci_failed` PR 执行以下决策：

| Fix PR 状态 | 动作 |
|------------|------|
| 不存在 | dispatch ci-log-analysis（首次修复） |
| open + `ci_successful` | 评论原始 PR，通知 reviewer 合并（一次性） |
| open + `ci_processing` | CI 运行中，跳过等待 |
| open + `ci_failed`，次数 < 3 | 重新 dispatch ci-log-analysis |
| open + `ci_failed`，次数 ≥ 3 | 关闭 Fix PR，通知人工介入 |
| open + 无状态 label | CI 尚未开始，跳过 |
| closed | 重新 dispatch（可能被人工关闭） |
| merged | 已合并，跳过 |

### ci-log-analysis 阶段

AI 诊断师（`.github/agents/ci-failure-analyst.md`）执行以下步骤：

1. 从 PR 评论中提取实际构建 job 的 Jenkins URL（**排除 trigger/编排层 URL**，只取 x86-64、aarch64 等架构专属 job 的日志）
2. 拉取控制台日志，提取错误行 + 末尾 300 行
3. 结合 PR diff 和历史失败模式知识库（`docs/ci-failure-patterns.md`）输出结构化诊断报告
4. 报告存入 `ci-fix-log` 分支的 `{pr-number}/ci-analysis.md`

> **关键约束**：若日志末尾显示 `Finished: SUCCESS` 但 PR 仍带 `ci_failed` label，说明实际失败在下游 job 中，此时诊断报告标记"证据不足"，不做任何猜测性修复。

### code-fix 阶段

代码修复工程师（`.github/agents/code-fixer.md`）基于诊断报告：

1. 克隆目标仓库，切换到 `fix/<pr-number>` 分支
2. 按照诊断报告中的修复方向实施最小化改动
3. git commit + push 到 fork 仓库
4. 若 Fix PR 不存在则创建（标题格式：`fix: <软件名> <版本> (fix #<原PR号>)`）

### 知识积累

每次修复完成后自动更新 `docs/ci-failure-patterns.md`（main 分支）：新案例归入已有模式章节，若是全新失败类型则新建章节，下次分析自动参考。

---

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
| `claude-sonnet-4-6` | 推荐，速度与质量均衡 |
| `claude-opus-4-8` | 最强推理，适合复杂修复场景 |
| `claude-haiku-4-5-20251001` | 最快，适合简单 lint / 格式修复 |

---

## CI Label 约定

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

---

## 跳过规则

Monitor 轮询时，以下类型的 PR 会被自动跳过，不触发修复：

| 规则 | 匹配条件 | 原因 |
|------|----------|------|
| **预发布版本** | 标题含 `-alpha`、`-beta`、`-rc`、`-preview`、`-dev`、`-snapshot`、`-nightly`（大小写不限，需 `-` 或 `.` 前缀） | 预发布版本通常不稳定，不值得自动修复 |
| **Fix PR 自身** | 标题以 `fix:` 开头（大小写不限） | 本工作流创建的 Fix PR 通过追加 commit 自行重试，不应递归触发 |

示例（跳过）：

```
【自动升级】etcd容器镜像升级至3.8.0-alpha.0版本.  → 跳过（预发布）
fix: etcd 3.6.11 (fix #2534)                     → 跳过（Fix PR）
```

示例（处理）：

```
【自动升级】etcd容器镜像升级至3.6.11版本.           → 正常处理
【自动升级】nginx容器镜像升级至1.25.3版本.          → 正常处理
```

---

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
│   │   ├── ci_data.py              # 分支读写：ci-fix-log + main（知识库）
│   │   ├── fix_pr_body.py          # Fix PR 标题与正文生成
│   │   ├── stage_common.py         # 阶段脚本公共工具
│   │   └── discover_conventions.py # 自动读取源仓库项目规范
│   ├── stages/
│   │   ├── ci-log-analysis.py      # 阶段1: CI 日志分析
│   │   └── code-fix.py             # 阶段2: 代码修复
│   └── watch/
│       ├── process_pr_events.py    # PR 轮询 + dispatch 决策逻辑
│       └── sync_poll_interval.py   # 同步 watchlist → cron 表达式
├── tests/
│   ├── __init__.py
│   ├── test_ci_gitcode_api.py      # URL 评分与日志抓取逻辑测试（84 个用例）
│   ├── test_fix_pr_body.py         # Fix PR 标题/正文生成测试（20 个用例）
│   └── test_process_pr_events.py   # 跳过规则测试（预发布 + fix: 前缀）
└── requirements.txt
```

### 关键数据分支

| 分支 | 内容 | 维护方式 |
|------|------|----------|
| `main` | 工作流代码 + `docs/ci-failure-patterns.md`（知识库） | 每次修复后自动追加 |
| `ci-fix-log` | `{pr-number}/ci-analysis.md`（诊断报告）+ `fix-summary.md`（修复摘要） | 每次修复后自动写入 |

---

## 常见问题

### Q: 日志抓取逻辑是如何工作的？

openEuler CI 评论表格中同时包含 trigger/编排层 URL 和各架构构建 URL（x86-64、aarch64 等）。系统通过以下策略确保拿到真正的构建日志：

1. **排除 trigger/编排层**：含 `/trigger/`、`/gate/`、`/pre-check/` 路径的 URL 直接丢弃——trigger 日志只含调度结果，其 `Finished: SUCCESS` 不代表构建成功
2. **逐行匹配**：按 HTML 表格行（`<tr>`）解析，URL 与同行的 FAILED/SUCCESS 关键词绑定，避免将成功架构的 URL 误判为失败
3. **架构优先**：含 `x86-64`、`aarch64` 等架构标识的 URL 优先于无架构标识的 URL

### Q: 为什么有时显示"证据不足"？

如果拉到的日志末尾是 `Finished: SUCCESS`，但 PR 仍有 `ci_failed` label，说明实际失败发生在未提供的下游 job 中（常见于 Jenkins 多架构并行构建场景）。此时诊断报告会主动标记"证据不足"，并说明需要获取哪个架构 job 的日志，而不会将日志中的 Warning 误判为根因。

### Q: Fix PR CI 失败后会如何？

Fix PR 被赋予 `ci_failed` label 后，下次轮询时系统会对该 Fix PR 的上游原始 PR 重新发起 ci-log-analysis，AI 根据新的失败日志追加 commit，无需创建新 PR。超过 3 次仍失败时自动关闭 Fix PR 并评论通知人工介入。

### Q: 怎么让某条 PR 不被修复？

有两种方式：
- **临时**：手动移除该 PR 的 `ci_failed` label
- **永久规则**：若是预发布版本（`-alpha`/`-beta`/`-rc` 等）或 `fix:` 前缀 PR，系统会自动跳过，详见[跳过规则](#跳过规则)

### Q: 如何新增一个监控仓库？

1. 确认目标仓库已按[CI Label 约定](#ci-label-约定)为 PR 打 label
2. 在 `config/watchlist.json` 的 `watched_repos` 数组中添加一条记录
3. 若是 GitCode 仓库，确认 `GITCODE_TOKEN` secret 和 `GITCODE_FORK_REPO` variable 已配置
4. 推送后自动生效，无需重启任何服务

### Q: 知识库（ci-failure-patterns.md）是如何更新的？

每次 code-fix 阶段完成后，AI 自动将本次案例归入 `docs/ci-failure-patterns.md` 对应模式章节；若是全新失败类型则新建章节。所有 ci-log-analysis 调用都会在 prompt 中携带最新知识库内容，实现经验复用。

### Q: 如何本地测试日志抓取逻辑？

```bash
export GITCODE_TOKEN=<your-token>
python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from scripts.lib.ci_gitcode_api import get_latest_failed_run, get_failed_job_logs
run = get_latest_failed_run('openeuler/openeuler-docker-images', '<head-sha>', '<token>', pr_number=2546)
print(run)
log = get_failed_job_logs('openeuler/openeuler-docker-images', 0, '<token>', target_url=run['target_url'])
print(log[:2000])
EOF
```

---

## 开发说明

### 运行测试

```bash
python3 -m pytest tests/ -v
```

测试集覆盖：

| 文件 | 覆盖范围 |
|------|----------|
| `test_ci_gitcode_api.py` | URL 评分（`_url_score`）、评论解析（`_find_jenkins_url_in_comments`）、`get_latest_failed_run` 完整逻辑，含混合 SUCCESS/FAILED 表格场景 |
| `test_fix_pr_body.py` | Fix PR 标题提取（软件名 + 版本）、正文结构、ci-data 读取 fallback |
| `test_process_pr_events.py` | 预发布版本检测（含大小写、点分隔、软件名误判边界）、`fix:` 前缀跳过逻辑 |

### API 层说明

| 模块 | 用途 |
|------|------|
| `ci_gitcode_api.py` | GitCode v5 API（PR 读写、评论）+ Jenkins 日志抓取 |
| `ci_github_api.py` | GitHub REST API（PR 读写） |
| `ci_api.py` | 平台工厂，根据 repo URL 自动分发到对应 API 模块 |
| `ci_data.py` | ci-fix-log 分支和 main 分支的文件读写，通过 GitHub Contents API 实现 |

### 技术栈

- **GitHub Actions**：工作流编排 + cron 调度
- **Python 3.11**：阶段脚本 + 工具库
- **OpenCode / Claude Code**：AI 模型调用（可切换）
- **GitHub Contents API**：ci-fix-log 分支（per-PR 分析报告）+ main 分支（失败模式知识库）读写
- **GitCode API v5**：PR 读写、评论、标签（Gitee-compatible）
- **GitCode API v4**：Pipeline / Job 日志获取（GitLab-compatible）

## License

MIT
