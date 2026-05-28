# dev-workflow

基于 GitHub Actions 和 AI 大模型的自动化技术设计工作流系统。

## 功能特性

- **自动化技术设计流程**：当 Issue 被标记为指定标签或用户评论 `/analyze` 时，自动触发 AI 分析流程
- **多阶段智能分析**：通过 AI agent 依次执行 3 个阶段的技术设计分析
  - req-analysis：需求分析
  - arch-design：架构设计
  - arch-review：架构评审
- **交互式进度管理**：自动维护 Issue 评论中的进度看板，实时更新分析状态
- **人工审核关卡**：在关键节点设置审核关卡，确保设计质量
- **命令控制**：支持通过 Issue 评论中的命令控制流程
- **跨仓库监控**：支持从其他仓库触发 AI 分析流程
- **灵活触发模式**：支持 label 触发、命令触发、混合触发三种模式
- **Stuck 检测**：自动检测长时间运行未完成的阶段，标记失败并通知用户

## 项目结构

```
.
├── .github/
│   ├── agents/              # AI Agent 提示词配置
│   │   ├── requirement-analyst.md
│   │   ├── architect.md
│   │   └── architecture-reviewer.md
│   │   └── phase0-clarification.md
│   └── workflows/
│       ├── stream-events.yml          # Issue 监控工作流
│       └── tech-design-trigger.yml    # AI 分析链路工作流
├── config/
│   └── watchlist.json                 # 监控仓库配置
├── scripts/
│   ├── lib/                           # Python 工具库
│   │   ├── state_machine.py           # 状态机权威定义（phase名、label正则、命令映射）
│   │   ├── github_api.py
│   │   ├── issue_tracker.py
│   │   ├── opencode_run.py
│   │   ├── phase_helper.py
│   │   ├── stage_common.py
│   │   ├── work_context.py
│   │   └── discover_conventions.py
│   ├── stages/                        # 各阶段执行脚本
│   │   ├── 01-requirements-analysis.py
│   │   ├── 02-architecture-design.py
│   │   └── 03-architecture-review.py
│   └── watch/
│       └── process_events.py          # Issue 监控 + 命令处理
├── requirements.txt
└── config/watchlist.json
```

## 状态机与 Label 体系

所有状态定义集中管理在 `scripts/lib/state_machine.py`，其他模块统一引用。

### Phase 语义化命名

| Phase ID | 中文名 | 旧名称 | Label 示例 |
|---|---|---|---|
| `req-analysis` | 需求分析 | phase1 | `ai-req-analysis`, `ai-req-analysis-done` |
| `arch-design` | 架构设计 | phase2 | `ai-arch-design`, `ai-arch-design-fail` |
| `arch-review` | 架构评审 | phase3 | `ai-arch-review`, `ai-arch-review-done` |

### 状态流转

```
/analyze（未追踪）→ init → req-analysis（自动）→ arch-design（/accept）→ arch-review（自动）→ design-done（/accept）
                                        ↓ fail                ↓ fail              ↓ fail
                                    /retry 或 /skip        /retry 或 /skip      /retry 或 /skip
```

- `init` 到 `req-analysis` 自动推进
- `req-analysis-done` 到 `arch-design` 需用户 `/accept` 确认
- `arch-design-done` 到 `arch-review` 自动推进（AI 自动进行架构评审）
- `arch-review-done` 到 `design-done` 需用户 `/accept` 确认（人工最终确认，标记为 `ai-design-done`）
- 在 `ai-design-done` 状态下 `/retry` 可重跑架构评审

### 控制命令

| 命令 | 说明 |
|------|------|
| `/analyze` | 启动分析（未追踪的 Issue，命令触发模式下使用） |
| `/accept` | 确认当前阶段完成，进入下一阶段 |
| `/retry` | 重跑当前失败阶段，或在 `ai-design-done` 状态下重跑架构评审 |
| `/skip` | 跳过当前失败/完成阶段 |
| `/retry-req` | 重跑需求分析 |
| `/retry-arch` | 重跑架构设计 |
| `/retry-review` | 重跑架构评审 |

## 使用方法

### 触发模式

`config/watchlist.json` 中每个仓库支持 `trigger_mode` 配置：

| trigger_mode | 说明 |
|---|---|
| `label` | **默认**：有 trigger_labels 的 Issue 自动触发 |
| `command` | 仅当用户在 Issue 评论 `/analyze` 才触发 |
| `both` | 同时支持 label 自动触发和 `/analyze` 命令触发 |

### 方式一：本仓库内使用

1. 在 dev-workflow 仓库中创建 Issue
2. 为 Issue 添加 `feature` 或 `bug` 标签（或在评论中 `/analyze`）
3. AI 将自动开始执行技术设计分析流程

### 方式二：跨仓库监控（推荐，零配置）

**优势：**
- ✅ 源仓库无需任何配置和工作流
- ✅ 所有 AI 分析在 dev-workflow 仓库执行，集中管理
- ✅ 只需在 dev-workflow 中维护监控列表

#### 1. 配置 GitHub Token

**在 dev-workflow 仓库中配置：**
- 创建 Personal Access Token (PAT)
  - 权限：`repo` + `workflow`
  - 路径：GitHub Settings → Developer settings → Personal access tokens
- 添加到仓库 Secrets
  - 路径：dev-workflow 仓库 → Settings → Secrets and variables → Actions
  - Name: `WATCH_TOKEN`（推荐）或 `DISPATCH_TOKEN`
  - Secret: 粘贴生成的 token

#### 2. 配置监控仓库列表

编辑 `config/watchlist.json`，添加需要监控的仓库：

```json
{
  "watched_repos": [
    {
      "repo": "owner/repo-name",
      "trigger_labels": ["feature", "bug"],
      "trigger_mode": "label",
      "enabled": true,
      "description": "项目描述"
    }
  ],
  "settings": {
    "poll_interval_minutes": 5,
    "max_events_per_run": 50,
    "lookback_minutes": 10
  }
}
```

**配置说明：**

| 字段 | 说明 | 示例 |
|------|------|------|
| `repo` | 仓库地址 | `owner/repo-name` |
| `trigger_labels` | 触发标签 | `["feature", "bug"]` |
| `trigger_mode` | 触发模式 | `label` / `command` / `both` |
| `enabled` | 是否启用 | `true` / `false` |

#### 3. 提供项目规范（可选但推荐）

在**源仓库**中提供以下文件（dev-workflow 会自动读取）：

| 文件路径 | 用途 | 优先级 |
|---------|------|--------|
| `README.md` | 项目说明、技术栈 | ⭐⭐⭐ |
| `docs/ARCHITECTURE.md` 或 `ARCHITECTURE.md` | 架构文档 | ⭐⭐⭐ |
| `CONTRIBUTING.md` 或 `.github/CONTRIBUTING.md` | 贡献指南、代码规范 | ⭐⭐ |
| `docs/CODE_STYLE.md` 或 `CODE_STYLE.md` | 代码风格规范 | ⭐⭐ |
| `CLAUDE.md` 或 `.cursorrules` | AI 开发规则 | ⭐⭐⭐ |
| `package.json` / `requirements.txt` | 技术栈信息 | ⭐ |

AI 会在分析时自动读取并遵守这些规范。

#### 4. 使用

**label 模式（默认）：**

1. 在源仓库创建 Issue
2. 添加 `feature` 或 `bug` 标签
3. 等待最多 5 分钟（轮询间隔），自动触发

**command 模式：**

1. 在源仓库创建 Issue
2. 在 Issue 评论中输入 `/analyze`
3. 等待最多 5 分钟，自动触发

触发后：
- ✅ 源 Issue 被打上 `ai-pending` 标签
- ✅ 源 Issue 收到进度看板评论
- ✅ dev-workflow 仓库开始执行 AI 分析
- ✅ AI 会读取并遵守项目规范

## 环境要求

- Python 3.11+
- GitHub Actions 运行环境
- AI 模型配置（通过 GitHub Variables 和 Secrets 设置）

### 环境变量

在仓库 Settings → Secrets and variables → Actions 中配置：

#### Variables（公开配置）

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AI_MODEL` | AI 模型名称 | `alibaba-cn/glm-5.1` |
| `AI_AGENT` | AI Agent 类型 | `build` |
| `AI_EXTRA_ARGS` | AI 运行额外参数 | `--dangerously-skip-permissions` |
| `OPENCODE_TIMEOUT_MS` | OpenCode 超时时间（毫秒） | `600000` (10分钟) |
| `OPENAI_BASE_URL` | AI API 基础地址（可选） | 留空使用默认地址 |

#### Secrets（敏感配置）

| Secret 名称 | 说明 | 必需 |
|-------------|------|------|
| `OPENAI_API_KEY` | AI 模型的 API 密钥 | ✅ **必需** |
| `WATCH_TOKEN` | 监控仓库的 GitHub Token | ✅ **必需** |
| `DISPATCH_TOKEN` | 跨仓库操作的 GitHub Token（可选） | 可选 |

### AI API Key 配置说明

**获取 API Key：**

根据你的 AI 模型提供商获取 API Key：

| 提供商 | 获取地址 | 示例 |
|--------|---------|------|
| 阿里通义 | https://bailian.console.aliyun.com/ | `sk-xxxxx` |
| OpenAI | https://platform.openai.com/api-keys | `sk-proj-xxxxx` |
| 智谱 AI | https://open.bigmodel.cn/ | `xxxxx.xxxxx` |
| 其他兼容 OpenAI 接口的服务 | - | - |

**配置步骤：**

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Secret: 粘贴你的 API Key
5. 点击 **Add secret**

**可选：配置自定义 API 地址**

如果使用其他兼容 OpenAI 接口的服务：

1. 点击 **New repository variable**
2. Name: `OPENAI_BASE_URL`
3. Value: `https://your-api-endpoint.com/v1`
4. 点击 **Add variable**

## 故障排查

### Dispatch 失败（HTTP 401/403）
- 检查 `DISPATCH_TOKEN` 是否正确配置
- 确认 token 有 `repo` 和 `workflow` 权限

### 目标仓库未收到 dispatch
- 检查源仓库 Actions 日志
- 确认目标仓库地址是否正确

### 工作流未触发
- label 模式：确认 Issue 标签是否为 `feature` 或 `bug`
- command 模式：确认是否评论了 `/analyze`
- 检查工作流文件是否正确部署

### Stuck 检测
- 如果某个阶段运行超过 60 分钟仍未完成，系统会自动标记为失败
- 查看 Issue 评论中的 stuck 通知，使用 `/retry` 或 `/skip` 处理

更多详细信息请参考 [CROSS-REPO-SETUP.md](file:///Users/zhengzhenyu/work/dev-workflow/CROSS-REPO-SETUP.md)

## 技术栈

- **GitHub Actions**：工作流编排
- **Python**：阶段脚本执行
- **OpenCode**：AI 模型调用
- **GitHub API**：Issue 管理和评论更新