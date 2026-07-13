# CI 失败分析报告

## 基本信息
- PR: #3121 — chore(claude-code): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 下载脚本被区域封禁
- 新模式症状关键词: App unavailable in region, syntax error near unexpected token `<`, install.sh, HTML, geo-blocked

## 根因分析

### 直接错误
```
#9 [3/7] RUN curl -fsSL -H "User-Agent: ..." "https://claude.ai/install.sh" -o /tmp/claude-install.sh && ...
#9 0.552 /tmp/claude-install.sh: line 1: syntax error near unexpected token `<'
#9 0.552 /tmp/claude-install.sh: line 1: `<!DOCTYPE html><!-- Last Published: Thu Jul 09 2026 ... --><html ...><title>App unavailable in region | Claude by Anthropic</title>...'
#9 ERROR: process "/bin/sh -c curl -fsSL ... "https://claude.ai/install.sh" ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/claude-code/2.1.20/24.03-lts-sp4/Dockerfile:17`（`RUN curl -fsSL "${CLAUDE_INSTALL_SCRIPT}" ...` 步骤，即第3个 RUN 指令）
- 失败原因: CI 构建环境所在区域无法访问 `https://claude.ai/install.sh`，Anthropic 服务器返回了一个 HTML 错误页面（标题为"App unavailable in region"）而非 bash 安装脚本。`curl` 将该 HTML 页面保存为 `/tmp/claude-install.sh`，随后 `bash` 尝试执行时因 HTML 标签（`<!DOCTYPE html>`）触发语法错误。

### 与 PR 变更的关联
- **直接相关**。PR 新增的 Dockerfile 中硬编码了 `https://claude.ai/install.sh` 作为安装脚本下载源。该 URL 在 CI 构建环境所在区域（推断为亚太/中国区域）被 Anthropic 做了地理限制，返回的是区域不可用提示页面而非实际安装脚本。这是 PR 新增代码触发的失败，但根因在于上游服务的区域访问策略与 CI 环境不兼容。

## 修复方向

### 方向 1（置信度: 高）
将 claude-code 的安装方式从"运行时从 `claude.ai` 下载安装脚本"改为"在 Dockerfile 中预置安装脚本或将安装脚本托管在 CI 环境可访问的镜像源"。具体而言：
- 将 `claude.ai/install.sh` 脚本内容直接内联到 Dockerfile 中（若脚本内容稳定且许可允许），或
- 将安装脚本上传至 CI 环境可访问的内部/镜像服务器，并修改 `CLAUDE_INSTALL_SCRIPT` ARG 指向新地址，或
- 使用支持该区域的代理/镜像 URL 替代 `https://claude.ai/install.sh`

### 方向 2（置信度: 中）
检查是否存在 Anthropic 官方提供的区域中立 CDN 地址或 GitHub Releases 发布的 claude-code 二进制包。如果 claude-code 在 GitHub 上有 release，可以直接从 GitHub 下载二进制，绕过 `claude.ai` 的地理限制。

## 需要进一步确认的点
- 确认 CI 构建环境的具体地理位置/网络出口，以判断是否有可用的代理或镜像方案
- 确认 `https://claude.ai/install.sh` 脚本内容是否稳定，是否适合内联或缓存到内部仓库
- 确认 claude-code 是否有 GitHub Releases 或其他无地理限制的下载渠道
- 确认同类镜像（如 AI 目录下其他依赖外网下载的镜像）是否有类似的地理限制处理方案可参考

## 修复验证要求
若修复方向涉及将安装脚本内联或托管到内部源，code-fixer 必须：
1. 从可访问 `https://claude.ai/install.sh` 的网络环境获取脚本的实际内容，验证脚本完整性后再内联或上传
2. 在修复后，确保 CI 构建流程中不再依赖 `claude.ai` 域名的直接 HTTP 访问
