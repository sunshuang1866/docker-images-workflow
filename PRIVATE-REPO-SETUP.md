# 私仓配置指南：PAT 权限与 Secrets 配置

本文档详细说明如何在个人私有仓库中配置 dev-workflow 跨仓库 AI 分析功能。

---

## 目录

1. [创建 Personal Access Token (PAT)](#1-创建-personal-access-token-pat)
2. [在私仓中配置 Secrets](#2-在私仓中配置-secrets)
3. [在源仓库中配置 Secrets](#3-在源仓库中配置-secrets)
4. [配置环境变量](#4-配置环境变量)
5. [部署工作流文件](#5-部署工作流文件)
6. [验证配置](#6-验证配置)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 创建 Personal Access Token (PAT)

### 步骤 1：进入 Token 创建页面

1. 登录 GitHub
2. 点击右上角头像 → **Settings**
3. 左侧菜单找到 **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token** → **Generate new token (classic)**

### 步骤 2：配置 Token 信息

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| **Note** | `dev-workflow-cross-repo` | Token 名称，便于识别 |
| **Expiration** | `90 days` 或 `No expiration` | 根据安全要求选择 |

### 步骤 3：选择权限（关键步骤）

根据你的使用场景选择权限：

#### 最小权限配置（推荐）

```
✅ repo
  ✅ repo:status
  ✅ repo_deployment
  ✅ public_repo
  ✅ repo:invite
  
✅ workflow          # 触发工作流必须
  
✅ read:org          # 如果是组织仓库需要此项
```

#### 完整权限配置（如果遇到问题可使用）

```
✅ repo              # 完整仓库访问权限
✅ workflow          # 工作流权限
✅ admin:repo_hook   # Webhook 管理（可选）
✅ read:org          # 组织读取（如需要）
```

### 步骤 4：生成并保存 Token

1. 滚动到页面底部，点击 **Generate token**
2. ⚠️ **立即复制 Token 值**（离开页面后无法再次查看）
3. 保存到安全的地方（如密码管理器）

**Token 格式示例：** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 2. 在私仓中配置 Secrets

### 步骤 1：进入私仓 Settings

1. 打开你的私有仓库页面
2. 点击顶部 **Settings** 标签

### 步骤 2：添加 Secrets

1. 左侧菜单找到 **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下 Secret：

| Secret 名称 | 值 | 说明 |
|-------------|-----|------|
| `DISPATCH_TOKEN` | 步骤 1 中创建的 PAT | 用于跨仓库通信 |

### 步骤 3：验证添加

添加完成后，你应该在 Secrets 列表中看到：
```
DISPATCH_TOKEN  (Added just now)
```

⚠️ **注意：** Secrets 的值是加密的，添加后无法查看，只能重新设置。

---

## 3. 在源仓库中配置 Secrets

对**每个需要监控的源仓库**重复以下步骤：

### 步骤 1：进入源仓库 Settings

1. 打开源仓库页面
2. 点击顶部 **Settings** 标签

### 步骤 2：添加 Secrets

1. 左侧菜单找到 **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下 Secret：

| Secret 名称 | 值 | 说明 |
|-------------|-----|------|
| `DISPATCH_TOKEN` | 步骤 1 中创建的 PAT（同一个） | 用于发送 dispatch |

### 步骤 3：验证权限

确保 PAT 对源仓库有 **读取权限**：
- 如果源仓库是公开的，PAT 至少有 `public_repo` 权限即可
- 如果源仓库也是私有的，PAT 必须有 `repo` 权限

---

## 4. 配置环境变量

在**私仓**中配置以下环境变量（Settings → Secrets and variables → Actions → Variables）：

| 变量名 | 推荐值 | 说明 |
|--------|--------|------|
| `AI_MODEL` | `alibaba-cn/glm-5.1` | AI 模型名称 |
| `AI_AGENT` | `build` | AI Agent 类型 |
| `AI_EXTRA_ARGS` | `--dangerously-skip-permissions` | AI 运行参数 |
| `OPENCODE_TIMEOUT_MS` | `1800000` | 超时时间（30 分钟） |

### 添加步骤

1. 在私仓 Settings → Secrets and variables → Actions
2. 切换到 **Variables** 标签
3. 点击 **New repository variable**
4. 填写名称和值，点击 **Add variable**

---

## 5. 部署工作流文件

### 5.1 在私仓中部署

将以下文件复制到私仓：

```
私仓/
└── .github/
    └── workflows/
        └── tech-design-trigger.yml    # 主工作流（从 dev-workflow 复制）
```

同时复制以下目录：
```
私仓/
├── .github/
│   ├── agents/                        # AI Agent 提示词
│   │   ├── phase0-clarification.md
│   │   ├── requirement-analyst.md
│   │   ├── architect.md
│   │   └── architecture-reviewer.md
└── scripts/                           # Python 脚本
    ├── lib/
    └── stages/
```

### 5.2 在源仓库中部署

将以下文件复制到源仓库：

```
源仓库/
└── .github/
    └── workflows/
        └── cross-repo-dispatch.yml    # 触发工作流
```

### 5.3 修改目标仓库地址

编辑 `cross-repo-dispatch.yml`，找到以下行并修改为你的私仓地址：

```yaml
# 原内容（约第 88 行）
https://api.github.com/repos/ZhengZhenyu/dev-workflow/dispatches

# 修改为
https://api.github.com/repos/你的用户名/你的私仓名/dispatches
```

---

## 6. 验证配置

### 6.1 测试 Token 权限

在本地或 CI 中运行以下命令验证 Token 是否有效：

```bash
# 测试读取源仓库
curl -H "Authorization: token gp_your_token" \
     https://api.github.com/repos/你的用户名/源仓库

# 测试触发私仓 dispatch
curl -X POST \
     -H "Authorization: token gp_your_token" \
     -H "Accept: application/vnd.github.everest-preview+json" \
     -H "Content-Type: application/json" \
     https://api.github.com/repos/你的用户名/私仓名/dispatches \
     -d '{"event_type":"test"}'
```

期望返回：`204 No Content`

### 6.2 端到端测试

1. 在源仓库创建一个测试 Issue
2. 添加 `rfc` 标签
3. 观察：
   - ✅ 源仓库 Actions 中 `cross-repo-dispatch` 工作流是否成功
   - ✅ 私仓 Actions 中 `tech-design-trigger` 工作流是否被触发
   - ✅ 源仓库 Issue 是否收到进度看板评论

---

## 7. 常见问题排查

### 问题 1：Dispatch 返回 401/403

**可能原因：**
- Token 无效或已过期
- Token 缺少目标仓库权限

**解决方法：**
1. 检查 Token 是否过期
2. 确认 Token 有 `workflow` 权限
3. 重新生成 Token 并更新 Secrets

### 问题 2：Dispatch 成功但私仓未触发

**可能原因：**
- 私仓中没有对应的工作流文件
- 工作流文件名或事件类型不匹配

**解决方法：**
1. 确认 `tech-design-trigger.yml` 存在于 `.github/workflows/`
2. 确认文件中包含：
   ```yaml
   on:
     repository_dispatch:
       types: [issue-trigger]
   ```
3. 检查私仓 Actions 页面是否有被禁用的工作流

### 问题 3：Checkout 源仓库失败

**可能原因：**
- Token 缺少源仓库读取权限
- 源仓库是私有仓库但 Token 只有 `public_repo` 权限

**解决方法：**
1. 确认 Token 有 `repo` 权限（完整仓库访问）
2. 如果源仓库是组织仓库，可能需要 `read:org` 权限

### 问题 4：AI 分析失败

**可能原因：**
- 环境变量未配置
- OpenCode 未正确安装
- AI 模型不可用

**解决方法：**
1. 检查私仓 Variables 中是否配置了 `AI_MODEL` 等变量
2. 查看 Actions 日志中的具体错误信息
3. 尝试更换 AI 模型

---

## 快速检查清单

在开始使用前，请确认：

- [ ] PAT 已创建且包含 `repo` + `workflow` 权限
- [ ] PAT 已保存到安全位置
- [ ] 私仓中已配置 `DISPATCH_TOKEN` Secret
- [ ] 私仓中已配置 `AI_MODEL` 等 Variables
- [ ] 源仓库中已配置 `DISPATCH_TOKEN` Secret
- [ ] 私仓中已部署 `tech-design-trigger.yml` 和 `agents/`、`scripts/`
- [ ] 源仓库中已部署 `cross-repo-dispatch.yml`
- [ ] `cross-repo-dispatch.yml` 中的目标仓库地址已修改为私仓
- [ ] 端到端测试通过

---

## 附录：权限对照表

| 操作 | 所需最小权限 | 说明 |
|------|-------------|------|
| 发送 repository_dispatch | `repo` 或 `workflow` | 需要目标仓库写入权限 |
| 接收 repository_dispatch | 无（工作流自动接收） | 工作流需存在于目标仓库 |
| Checkout 公开仓库 | `public_repo` | 仅读取代码 |
| Checkout 私有仓库 | `repo` | 需要完整仓库访问 |
| 操作 Issue（添加标签/评论） | `repo` | 需要仓库 Issue 权限 |
| 触发 Actions 工作流 | `workflow` | 需要工作流触发权限 |

---

**文档版本：** v1.0  
**最后更新：** 2026-05-27
