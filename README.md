# docker-images-workflow

基于 GitHub Actions 和 AI 大模型的 **PR CI 失败自动修复**工作流。

## 受众导航

| 你是… | 直接跳到 |
|-------|---------|
| **仓库维护者**（接入新仓库、配置 Secret、看工作流是否正常运行） | [快速开始](#快速开始) → [CI Label 约定](#ci-label-约定) → [常见问题](#常见问题) |
| **开发者**（修改代码、新增功能、写测试） | [目录结构](#目录结构) → [模块说明](#模块说明) → [开发指南](#开发指南) |

## 目录

- [概述](#概述)

**仓库维护者**
- [快速开始](#快速开始)
- [工作流程](#工作流程)
- [跳过规则](#跳过规则)
- [AI 后端配置](#ai-后端配置)
- [CI Label 约定](#ci-label-约定)
- [常见问题](#常见问题)

**开发者**
- [目录结构](#目录结构)
- [模块说明](#模块说明)
- [开发指南](#开发指南)

## 概述

### 背景

开源社区的容器镜像仓库（如 openeuler/openeuler-docker-images）通过 PR 持续更新软件版本。版本升级 PR 经常因构建环境、依赖、编译参数等变化导致 CI 失败，需要维护者人工分析日志、定位根因、修改 Dockerfile 并重新提交。

这类工作高度重复，且模式固定——**根因往往是已知的构建失败模式**：缺少编译依赖、链接参数变更、Makefile 路径假设失效等。人工处理每条 PR 平均需要 15–30 分钟，严重拖慢合并节奏。

### 解决方案

docker-images-workflow 是一套面向容器镜像仓库的 **CI 失败自动修复流水线**，以 GitHub Actions 作为编排引擎，以 AI 大模型作为诊断和修复执行者。

**两阶段流水线：**

| 阶段 | 触发 | 执行内容 | 输出 |
|------|------|----------|------|
| **ci-log-analysis** | repository_dispatch | 拉取 Jenkins 构建日志 + PR diff，AI 分析根因，参考历史知识库 | 结构化诊断报告（ci-fix-log 分支） |
| **code-fix** | repository_dispatch | AI 基于诊断报告在源码中实施最小化修复，git commit + push | Fix PR（fork → 上游） |

**完整生命周期：**

```
目标仓库 PR 获得 ci_failed label
         ↓
Monitor 定时轮询 → 跳过规则过滤 → dispatch ci-log-analysis
         ↓
AI 诊断师：拉取架构构建 job 日志（排除 trigger 层）→ 诊断报告
         ↓
AI 修复工程师：按报告修改代码 → commit → push → Fix PR
         ↓
Fix PR CI 结果
  ├─ ci_successful ─→ 评论原始 PR，通知 review 合并 ✅
  ├─ ci_processing ─→ 等待，下次轮询再判断
  ├─ ci_failed（< 6 次）─→ 重新进入 ci-log-analysis
  └─ ci_failed（≥ 6 次）─→ 关闭 Fix PR，通知人工介入 ⚠️
```

### 核心能力

| 能力 | 说明 |
|------|------|
| **精准日志抓取** | 从 PR 评论表格中按行解析 FAILED/SUCCESS 状态，只取实际失败架构（x86-64、aarch64 等）的构建 job 日志，排除 trigger/编排层；日志内容若与 ci_failed 状态矛盾则主动标记证据不足 |
| **历史知识库** | `docs/ci-failure-patterns.md` 按失败模式分类，每次修复后自动追加新案例，下次分析自动参考，同类问题置信度显著提升 |
| **Fix PR 自管理** | Fix PR CI 再次失败时自动追加 commit 重试，无需创建新 PR；超过最大重试次数（默认 6 次）自动关闭并通知人工介入 |
| **多平台支持** | 同时兼容 GitCode 和 GitHub 仓库，通过 URL 自动识别平台，API 层完全隔离 |
| **智能跳过** | 预发布版本（-alpha/-beta/-rc 等）和工作流自身创建的 Fix PR 自动跳过，不触发修复链路 |

---

## 快速开始

### 1. Fork 本仓库

Fork `sunshuang1866/docker-images-workflow` 到你的 GitHub 账号，后续在 fork 仓库的 Actions 中运行。

### 2. 配置 Secrets

在 **Settings → Secrets and variables → Actions → Secrets** 中添加：

| Secret | 用途 | 必需 |
|--------|------|------|
| `DISPATCH_TOKEN` | GitHub 操作：触发 dispatch、ci-data 读写、checkout、推送代码、创建 PR | 必填（GitHub PAT，需 `repo` + `workflow` scope） |
| `GITCODE_TOKEN` | GitCode 仓库读写：克隆代码、读 PR/CI 日志、推送 fork、创建 PR、评论 | 监控 GitCode 仓库时必填 |
| `AI_API_KEY` | AI 模型 API Key | `AI_RUNNER=opencode` 时必填 |
| `CLAUDE_CREDENTIALS_JSON` | Claude.ai OAuth 凭证 | `AI_RUNNER=claude-code-account` 时必填，见 [AI 后端配置](#ai-后端配置) |

### 3. 配置 Variables

在 **Settings → Secrets and variables → Actions → Variables** 中添加：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_RUNNER` | AI 后端：`opencode` 或 `claude-code-account` | `opencode` |
| `AI_MODEL` | 模型名称 | `deepseek/deepseek-v4-pro` |
| `GITCODE_FORK_REPO` | GitCode fork 仓库路径（如 `yourname/repo`），为空时直接推送原仓库 | `''` |
| `GIT_COMMIT_NAME` | Fix commit 的 git user.name（CLA 合规时必填） | `github-actions[bot]` |
| `GIT_COMMIT_EMAIL` | Fix commit 的 git user.email | `github-actions[bot]@users.noreply.github.com` |

### 4. 添加监控仓库

编辑 `config/watchlist.json`，在 `watched_repos` 中添加目标仓库：

```json
{
  "watched_repos": [
    {
      "repo": "https://gitcode.com/openeuler/openeuler-docker-images",
      "trigger_labels": ["ci_failed"],
      "enabled": true,
      "description": "openEuler 容器镜像"
    }
  ],
  "settings": {
    "poll_interval_minutes": 5,
    "max_events_per_run": 50,
    "lookback_minutes": 60
  }
}
```

> 修改 `poll_interval_minutes` 会自动触发 `sync-poll-interval.yml`，将 cron 表达式同步到 `stream-pr-events.yml`，无需手动改 workflow 文件。平台识别：URL 含 `gitcode.com` 使用 GitCode API，否则使用 GitHub API。

### 5. 确认目标仓库 CI Label 约定

目标仓库的 CI 必须在对应时机打 label，详见 [CI Label 约定](#ci-label-约定)。配置完成后，等待下一次 cron 触发（或手动运行 `stream-pr-events.yml`）即可。

---

## 工作流程

### Monitor 轮询

`stream-pr-events.yml` 按 `poll_interval_minutes` 定时运行，对每条 `ci_failed` PR 执行以下决策：

| Fix PR 状态 | 动作 |
|------------|------|
| 不存在 | dispatch ci-log-analysis（首次修复） |
| open + `ci_successful` | 评论原始 PR，通知 reviewer 合并（一次性） |
| open + `ci_processing` | CI 运行中，跳过等待 |
| open + `ci_failed`，次数 < 6 | 重新 dispatch ci-log-analysis |
| open + `ci_failed`，次数 ≥ 6 | 关闭 Fix PR，通知人工介入 |
| open + 无状态 label | CI 尚未开始，跳过 |
| closed | 重新 dispatch（可能被人工关闭后需重试） |
| merged | 已合并，跳过 |

### ci-log-analysis 阶段

AI 诊断师（`.github/agents/ci-failure-analyst.md`）执行步骤：

1. **前置检查**：若日志末尾显示 `Finished: SUCCESS` 但 PR 仍有 `ci_failed` label，立即标记"证据不足"，不做分析——说明日志来自 trigger/编排层，实际失败在下游 job
2. **日志抓取**：从 PR 评论表格逐行解析，仅取 FAILED 行对应的架构构建 URL，排除 trigger/gate/pre-check 层 URL
3. **根因定位**：结合 PR diff 和历史知识库（`docs/ci-failure-patterns.md`）输出结构化诊断报告
4. **报告存储**：写入 ci-fix-log 分支的 `{pr-number}/ci-analysis.md`

### code-fix 阶段

代码修复工程师（`.github/agents/code-fixer.md`）执行步骤：

1. 克隆目标仓库，切换到 `fix/<pr-number>` 分支
2. 按照诊断报告的修复方向实施最小化改动
3. git commit + push 到 fork 仓库
4. 若 Fix PR 不存在则创建，标题格式：`fix: <软件名> <版本> (fix #<原PR号>)`

### 知识积累

每次修复完成后自动更新 `docs/ci-failure-patterns.md`（main 分支）：新案例归入已有模式章节，若是全新失败类型则新建章节，下次分析自动参考。

---

## 跳过规则

Monitor 轮询时，以下类型的 PR 自动跳过，不触发修复流水线：

| 规则 | 匹配条件 | 原因 |
|------|----------|------|
| **预发布版本** | 标题含 `-alpha`、`-beta`、`-rc`、`-preview`、`-dev`、`-snapshot`、`-nightly`（大小写不限，需 `-` 或 `.` 前缀，非软件名一部分） | 预发布版本通常不稳定，不值得自动修复 |
| **Fix PR 自身** | 标题以 `fix:` 开头（大小写不限，容忍前置空格） | 本工作流创建的 Fix PR 通过追加 commit 自行重试，不应递归触发 |
| **已有通过 CI 的修复** | 存在标题含 `(fix #<原PR号>)`、状态 open、且带 `ci_successful` label 的 PR | Fix PR 已通过 CI，等待 reviewer 合并，无需再次触发修复 |

**示例：**

| PR 标题 | 结果 |
|---------|------|
| `【自动升级】etcd容器镜像升级至3.8.0-alpha.0版本.` | 跳过（预发布）|
| `fix: etcd 3.6.11 (fix #2534)` | 跳过（Fix PR 自身）|
| 原始 PR #2534，已存在标题含 `(fix #2534)` 且 `ci_successful` 的 open PR | 跳过（已有通过 CI 的修复）|
| `【自动升级】etcd容器镜像升级至3.6.11版本.` | 正常处理 |
| `【自动升级】developer-tool升级至1.0.0版本.` | 正常处理（`developer-` 是软件名，非版本标记）|

---

## AI 后端配置

### 使用 OpenCode（默认）

OpenCode 兼容 OpenAI 接口，支持 DeepSeek、通义等模型。将 Variable `AI_RUNNER` 设为 `opencode`，`AI_MODEL` 填入对应模型名：

| 提供商 | `AI_MODEL` 示例 |
|--------|----------------|
| DeepSeek | `deepseek/deepseek-v4-pro` |
| 阿里通义 | `alibaba-cn/qwen-plus` |
| OpenAI | `openai/gpt-4o` |

### 使用 Claude Code（账号模式，无需 API Key）

适合已有 Claude Pro / Max 订阅的用户。将 `AI_RUNNER` 设为 `claude-code-account`，`AI_MODEL` 设为对应 Claude 模型名。

**一次性获取凭证：**

```bash
# 在本地登录 Claude Code（会引导浏览器 OAuth）
claude

# 查看凭证，将完整 JSON 内容存入 Secret CLAUDE_CREDENTIALS_JSON
cat ~/.claude/.credentials.json
```

> ⚠️ OAuth Token 会过期（通常数周至数月），过期后需重新登录并更新 Secret。

| `AI_MODEL` 示例 | 说明 |
|----------------|------|
| `claude-sonnet-4-6` | 推荐，速度与质量均衡 |
| `claude-opus-4-8` | 最强推理，适合复杂修复场景 |
| `claude-haiku-4-5-20251001` | 最快，适合简单 lint / 格式修复 |

---

## CI Label 约定

目标仓库的 CI 需在以下时机为 PR 打对应 label，本工作流依赖这些 label 判断 CI 状态：

| label | 打上时机 |
|-------|---------|
| `ci_failed` | CI 失败时 |
| `ci_processing` | CI 运行中时 |
| `ci_successful` | CI 通过时 |

**GitCode（GitLab CI）示例：**

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

**GitHub 示例：**

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

## 常见问题

### Q: 工作流运行了但没有触发修复，怎么排查？

按以下顺序检查：
1. 目标仓库的 PR 是否确实有 `ci_failed` label（不是 `ci_failed` 的拼写变体）
2. `config/watchlist.json` 中该仓库的 `enabled` 是否为 `true`
3. PR 标题是否匹配[跳过规则](#跳过规则)（预发布版本或 `fix:` 前缀）
4. `DISPATCH_TOKEN` / `GITCODE_TOKEN` 是否有足够权限
5. 在 Actions tab 查看 `stream-pr-events` 的运行日志，搜索 `→ Skipping` 或 `❌`

### Q: 日志抓取逻辑是怎么工作的？

openEuler CI 的 PR 评论表格中同时包含 trigger 层 URL 和各架构构建 URL，且路径深度相同，无法仅靠深度区分。系统采用以下策略：

1. **排除编排层**：含 `/trigger/`、`/gate/`、`/pre-check/` 路径的 URL 直接丢弃
2. **逐行解析**：按 HTML `<tr>` 行匹配 URL 与同行的 FAILED/SUCCESS/`&#10060;` 标记，避免将成功架构（x86-64 SUCCESS）的 URL 误判为失败 URL
3. **架构优先**：含 `x86-64`、`aarch64` 等架构标识的 URL 评分高于无标识 URL
4. **重试时用 Fix PR 评论**：首次分析从原始 PR 评论查 URL；重试时 CI 结果表格在 Fix PR 评论中，自动切换到 Fix PR 编号查询，确保每次都取最新构建的 URL
5. **日志截取策略**：取日志末尾 500 行（尾部优先），不再从全量日志提取 error 行——构建失败几乎总在日志末尾，早期 CMake 警告等噪声行曾挤占预算导致末尾关键段（如依赖下载失败）被截断

### Q: 诊断报告中出现"证据不足"，怎么处理？

说明拉到的日志末尾是 `Finished: SUCCESS`，与 PR 的 `ci_failed` 状态矛盾——实际失败发生在未暴露的下游 job。报告会说明需要哪个架构的 job URL，可以手动拿到该 URL 后参考报告中的提示定位问题。此情况通常由 Jenkins 多架构并行构建中只有部分架构失败引起。

### Q: Fix PR CI 失败后怎么处理？

无需手动操作。Fix PR 收到 `ci_failed` label 后，下次 Monitor 轮询时系统会对该 Fix PR 对应的**原始 PR** 重新发起 ci-log-analysis，AI 根据新的失败日志追加 commit 修复。超过 6 次后自动关闭 Fix PR 并评论通知人工介入。

### Q: 想手动跳过某条 PR，怎么做？

移除该 PR 的 `ci_failed` label 即可。下次轮询时不再出现在处理列表中。若需永久跳过所有预发布版本或 Fix PR，规则已内置，见[跳过规则](#跳过规则)。

### Q: 如何在本地测试日志抓取逻辑？

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from scripts.lib.ci_gitcode_api import get_latest_failed_run, get_failed_job_logs

TOKEN = 'your-gitcode-token'
REPO  = 'openeuler/openeuler-docker-images'

run = get_latest_failed_run(REPO, '<head-sha>', TOKEN, pr_number=2546)
print('selected URL:', run['target_url'])

log = get_failed_job_logs(REPO, 0, TOKEN, target_url=run['target_url'])
print(log[:3000])
EOF
```

---

## 目录结构

```
.
├── .github/
│   ├── agents/
│   │   ├── ci-failure-analyst.md   # AI Agent 1: CI 失败诊断师（含核心约束和分析方法）
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
│   │   ├── ci_gitcode_api.py       # GitCode API 封装（v5 PR + v4 Pipeline + Jenkins 日志）
│   │   ├── ci_data.py              # 分支读写：ci-fix-log + main（知识库）
│   │   ├── fix_pr_body.py          # Fix PR 标题与正文生成
│   │   ├── stage_common.py         # 阶段脚本公共工具
│   │   └── discover_conventions.py # 自动读取源仓库项目规范
│   ├── stages/
│   │   ├── ci-log-analysis.py      # 阶段1: CI 日志分析
│   │   └── code-fix.py             # 阶段2: 代码修复
│   └── watch/
│       ├── process_pr_events.py    # PR 轮询 + dispatch 决策 + 跳过规则
│       └── sync_poll_interval.py   # 同步 watchlist → cron 表达式
├── tests/
│   ├── __init__.py
│   ├── test_ci_gitcode_api.py      # URL 评分与日志抓取逻辑（84 个用例）
│   ├── test_fix_pr_body.py         # Fix PR 标题/正文生成（20 个用例）
│   └── test_process_pr_events.py   # 跳过规则（预发布 + fix: 前缀，95 个用例）
└── requirements.txt
```

### 关键数据分支

| 分支 | 内容 | 维护方式 |
|------|------|----------|
| `main` | 工作流代码 + `docs/ci-failure-patterns.md`（知识库） | 每次修复后自动追加新案例 |
| `ci-fix-log` | `{pr-number}/ci-analysis.md`（诊断报告）+ `fix-summary.md`（修复摘要） | 每次修复后由工作流写入 |

---

## 模块说明

### 工作流编排

| 文件 | 职责 |
|------|------|
| `stream-pr-events.yml` | cron 触发，调用 `process_pr_events.py` 扫描 ci_failed PR，决策 dispatch |
| `pr-ci-fix-trigger.yml` | 接收 dispatch，串行执行 ci-log-analysis → code-fix 两阶段 |
| `sync-poll-interval.yml` | 监听 `watchlist.json` 变更，自动更新 cron 表达式 |

### AI Agent Prompt

| 文件 | 职责 |
|------|------|
| `ci-failure-analyst.md` | 诊断师角色定义：错误类型分类、分析方法（含前置一致性检查）、输出结构、核心约束（禁止在 SUCCESS 日志中找根因） |
| `code-fixer.md` | 修复工程师角色定义：如何读取诊断报告、最小化修改原则、提交规范 |

### Python 库（`scripts/lib/`）

| 模块 | 职责 |
|------|------|
| `ci_gitcode_api.py` | GitCode v5（PR 读写、评论）+ Jenkins 日志抓取（逐行 URL 解析、编排层过滤、架构评分） |
| `ci_github_api.py` | GitHub REST API（PR 读写） |
| `ci_api.py` | 平台工厂，根据 repo URL 自动分发到对应 API 模块 |
| `ci_data.py` | ci-fix-log 分支和 main 分支的文件读写，通过 GitHub Contents API 实现 |
| `fix_pr_body.py` | 从诊断报告和修复摘要构建 Fix PR 标题（提取软件名+版本）与正文 |
| `ai_runner.py` | 根据 `AI_RUNNER` 环境变量分发到 opencode 或 claude-code 后端 |

### Jenkins 日志抓取核心逻辑

```
PR 评论 HTML 表格
  └─ 逐行（<tr>）解析
       ├─ 排除含 /trigger/ /gate/ /pre-check/ 的 URL（编排层）
       ├─ 同行含 FAILED / &#10060; → 加入 failed_urls
       └─ 否则 → 加入 other_urls
           ↓
candidates = failed_urls or other_urls
max(candidates, key=_url_score)   # 架构标识 > 路径深度 > 非编排层
```

---

## 开发指南

### 运行测试

```bash
python3 -m pytest tests/ -v
```

测试覆盖：

| 文件 | 覆盖范围 | 用例数 |
|------|----------|--------|
| `test_ci_gitcode_api.py` | `_url_score`、`_find_jenkins_url_in_comments`（含混合 SUCCESS/FAILED 表格）、`_fetch_external_ci_log`（尾部优先截取）、`find_open_ci_successful_fix_pr`、`get_latest_failed_run` 完整逻辑 | 44 |
| `test_fix_pr_body.py` | Fix PR 标题提取（软件名+版本）、正文结构、ci-data 读取 fallback | 22 |
| `test_process_pr_events.py` | 预发布版本检测（大小写/点分隔/软件名边界）、`fix:` 前缀跳过 | 41 |

### 新增监控平台

1. 在 `scripts/lib/` 下新建 `ci_{platform}_api.py`，实现与 `ci_github_api.py` 相同的接口
2. 在 `scripts/lib/ci_api.py` 的 `detect_platform` 和 `get_api` 中注册新平台
3. 无需修改任何阶段脚本，平台切换完全由工厂层处理

### 调整跳过规则

跳过规则集中在 `scripts/watch/process_pr_events.py` 的主循环中：

```python
if _is_prerelease(pr_title):          # 预发布版本检测
    ...
if pr_title.lstrip().lower().startswith('fix:'):  # Fix PR 过滤
    ...
```

新增规则在此处追加即可，并同步在 `tests/test_process_pr_events.py` 中覆盖。

### 技术栈

| 组件 | 用途 |
|------|------|
| GitHub Actions | 工作流编排 + cron 调度 + repository_dispatch |
| Python 3.11 | 阶段脚本 + 工具库 |
| OpenCode / Claude Code | AI 模型调用（可切换） |
| GitHub Contents API | ci-fix-log 分支（per-PR 报告）+ main 分支（知识库）读写 |
| GitCode API v5 | PR 读写、评论、标签（Gitee-compatible） |
| GitCode API v4 | Pipeline / Job 日志获取（GitLab-compatible） |

## License

MIT
