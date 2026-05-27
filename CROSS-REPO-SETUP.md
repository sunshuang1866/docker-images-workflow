# 跨仓库监控配置指南

## 概述

本方案实现了跨仓库的 Issue 监控：当**源仓库**的 Issue 被打上 `rfc` 或 `bug` 标签时，自动触发 **dev-workflow 仓库**中的 AI 分析流程。

## 架构

```
[源仓库 A] --(repository_dispatch)--> [dev-workflow 仓库]
     ↓                                      ↓
  Issue 事件                           AI 分析流程
```

## 配置步骤

### 1. 在 dev-workflow 仓库配置 Token

1. 创建一个 GitHub Personal Access Token (PAT)：
   - 进入 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 点击 "Generate new token (classic)"
   - 权限要求：
     - ✅ `repo` (完整仓库权限)
     - ✅ `workflow` (工作流权限)
   - 生成后复制 token

2. 将 token 添加到 dev-workflow 仓库的 Secrets：
   - 进入 dev-workflow 仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - Name: `DISPATCH_TOKEN`
   - Secret: 粘贴刚才生成的 token

### 2. 在源仓库配置 Token

1. 使用同一个 PAT（或创建一个新的）

2. 将 token 添加到源仓库的 Secrets：
   - 进入源仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - Name: `DISPATCH_TOKEN`
   - Secret: 粘贴 token

### 3. 部署工作流到源仓库

将 `cross-repo-dispatch.yml` 文件复制到源仓库的 `.github/workflows/` 目录：

```
源仓库/
└── .github/
    └── workflows/
        └── cross-repo-dispatch.yml
```

**注意**：需要修改文件中的目标仓库地址（如果不是 `ZhengZhenyu/dev-workflow`）：

```yaml
# 第 44 行附近
https://api.github.com/repos/YOUR-USERNAME/dev-workflow/dispatches
```

### 4. 自定义配置（可选）

如果需要修改触发条件，编辑 `cross-repo-dispatch.yml`：

```yaml
# 修改触发标签
if: |
  (github.event.action == 'labeled' && (github.event.label.name == 'rfc' || github.event.label.name == 'bug'))
```

## 使用方式

1. 在**源仓库**创建 Issue
2. 为 Issue 添加 `rfc` 或 `bug` 标签
3. 自动触发：
   - 源仓库 Issue 被打上 `ai-pending` 标签
   - 源仓库 Issue 收到进度看板评论
   - dev-workflow 仓库开始执行 AI 分析流程

## 监控源仓库列表

由于 `repository_dispatch` 是基于 token 授权的，任何拥有有效 token 的仓库都可以触发 dev-workflow。

**目前可触发 dev-workflow 的仓库：**
- 任何配置了 `DISPATCH_TOKEN` 和 `cross-repo-dispatch.yml` 的仓库

**如果要限制只允许特定仓库触发**，可以在 `tech-design-trigger.yml` 中添加条件：

```yaml
trigger-on-dispatch:
  runs-on: ubuntu-latest
  if: |
    github.event_name == 'repository_dispatch' &&
    github.event.client_payload.source_repo == 'owner/repo-name'
```

## 故障排查

### Dispatch 失败（HTTP 401/403）
- 检查 `DISPATCH_TOKEN` 是否正确配置
- 确认 token 有 `repo` 和 `workflow` 权限

### 目标仓库未收到 dispatch
- 检查目标仓库地址是否正确
- 查看源仓库的 Actions 日志

### 目标仓库工作流未触发
- 检查 `tech-design-trigger.yml` 是否包含 `repository_dispatch` 触发器
- 确认事件类型匹配（`issue-trigger`）
