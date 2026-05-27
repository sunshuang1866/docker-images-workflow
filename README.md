# dev-workflow

基于 GitHub Actions 和 AI 大模型的自动化技术设计工作流系统。

## 功能特性

- **自动化技术设计流程**：当 Issue 被标记为 `rfc` 或 `bug` 时，自动触发完整的 AI 分析流程
- **多阶段智能分析**：通过 AI agent 依次执行 5 个阶段的技术设计分析
  - Phase 0：需求澄清
  - Phase 1：需求分析
  - Phase 2：架构设计
  - Phase 3：架构评审
  - 最终设计文档生成
- **交互式进度管理**：自动维护 Issue 评论中的进度看板，实时更新分析状态
- **人工审核关卡**：在关键节点设置审核关卡，确保设计质量
- **命令控制**：支持通过 Issue 评论中的命令（`/accept`, `/retry`, `/retry-design`, `/retry-review`）控制流程
- **跨仓库监控**：支持从其他仓库触发 AI 分析流程

## 项目结构

```
.
├── .github/
│   ├── agents/              # AI Agent 提示词配置
│   │   ├── phase0-clarification.md
│   │   ├── requirement-analyst.md
│   │   ├── architect.md
│   │   └── architecture-reviewer.md
│   └── workflows/
│       ├── tech-design-trigger.yml   # 主工作流定义
│       └── cross-repo-dispatch.yml   # 跨仓库触发工作流
├── scripts/
│   ├── lib/                 # Python 工具库
│   │   ├── github_api.py
│   │   ├── opencode_run.py
│   │   ├── stage_common.py
│   │   └── work_context.py
│   └── stages/              # 各阶段执行脚本
│       ├── 00-phase0-clarification.py
│       ├── 01-requirements-analysis.py
│       ├── 02-architecture-design.py
│       └── 03-architecture-review.py
├── requirements.txt
└── CROSS-REPO-SETUP.md      # 跨仓库配置详细指南
```

## 使用方法

### 方式一：本仓库内使用

1. 在 dev-workflow 仓库中创建 Issue
2. 为 Issue 添加 `rfc` 或 `bug` 标签
3. AI 将自动开始执行技术设计分析流程

### 方式二：跨仓库监控（推荐）

当需要在其他仓库触发 AI 分析时：

#### 1. 配置 GitHub Token

**在 dev-workflow 仓库中配置：**
- 创建 Personal Access Token (PAT)
  - 权限：`repo` + `workflow`
  - 路径：GitHub Settings → Developer settings → Personal access tokens
- 添加到仓库 Secrets
  - 路径：dev-workflow 仓库 → Settings → Secrets and variables → Actions
  - Name: `DISPATCH_TOKEN`
  - Secret: 粘贴生成的 token

**在每个需要监控的源仓库中配置：**
- 使用同一个 PAT
- 添加到源仓库 Secrets
  - 路径：源仓库 → Settings → Secrets and variables → Actions
  - Name: `DISPATCH_TOKEN`
  - Secret: 粘贴 token

#### 2. 部署触发工作流到源仓库

将 [`.github/workflows/cross-repo-dispatch.yml`](file:///Users/zhengzhenyu/work/dev-workflow/.github/workflows/cross-repo-dispatch.yml) 复制到源仓库的对应位置：

```
源仓库/
└── .github/
    └── workflows/
        └── cross-repo-dispatch.yml
```

**重要**：编辑文件第 44 行，修改为目标仓库地址：
```yaml
https://api.github.com/repos/你的用户名/dev-workflow/dispatches
```

#### 3. 提供项目规范（可选但推荐）

为了让 AI 分析更贴合你的项目，建议在源仓库中提供以下文件（会自动识别）：

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

在**源仓库**中：
1. 创建 Issue
2. 添加 `rfc` 或 `bug` 标签
3. 自动触发：
   - ✅ 源 Issue 被打上 `ai-pending` 标签
   - ✅ 源 Issue 收到进度看板评论
   - ✅ dev-workflow 仓库开始执行 AI 分析
   - ✅ AI 会读取并遵守项目规范

### 控制命令

在 Issue 评论中使用以下命令控制流程：

| 命令 | 说明 |
|------|------|
| `/accept` | 从头开始完整分析 |
| `/retry` | 从上次中断处继续 |
| `/retry-design` | 重新运行架构设计阶段 |
| `/retry-review` | 重新运行架构评审阶段 |

## 环境要求

- Python 3.11+
- GitHub Actions 运行环境
- AI 模型配置（通过 GitHub Variables 设置）

### 环境变量

在仓库 Settings → Secrets and variables → Actions → Variables 中配置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AI_MODEL` | AI 模型名称 | `alibaba-cn/glm-5.1` |
| `AI_AGENT` | AI Agent 类型 | `build` |
| `AI_EXTRA_ARGS` | AI 运行额外参数 | `--dangerously-skip-permissions` |
| `OPENCODE_TIMEOUT_MS` | OpenCode 超时时间（毫秒） | `1800000` (30分钟) |

## 故障排查

### Dispatch 失败（HTTP 401/403）
- 检查 `DISPATCH_TOKEN` 是否正确配置
- 确认 token 有 `repo` 和 `workflow` 权限

### 目标仓库未收到 dispatch
- 检查源仓库 Actions 日志
- 确认目标仓库地址是否正确

### 工作流未触发
- 确认 Issue 标签是否为 `rfc` 或 `bug`
- 检查工作流文件是否正确部署

更多详细信息请参考 [CROSS-REPO-SETUP.md](file:///Users/zhengzhenyu/work/dev-workflow/CROSS-REPO-SETUP.md)

## 技术栈

- **GitHub Actions**：工作流编排
- **Python**：阶段脚本执行
- **OpenCode**：AI 模型调用
- **GitHub API**：Issue 管理和评论更新
