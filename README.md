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
│       └── tech-design-trigger.yml   # 主工作流定义
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
└── requirements.txt
```

## 使用方法

### 触发分析流程

1. 在仓库中创建 Issue
2. 为 Issue 添加 `rfc` 或 `bug` 标签
3. AI 将自动开始执行技术设计分析流程

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

## 技术栈

- **GitHub Actions**：工作流编排
- **Python**：阶段脚本执行
- **OpenCode**：AI 模型调用
- **GitHub API**：Issue 管理和评论更新
