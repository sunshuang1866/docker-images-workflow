# 修复摘要

## 修复的问题
Claude 安装脚本下载时遭服务器 403 拒绝，通过添加浏览器 User-Agent 请求头绕过 bot 检测。

## 修改的文件
- `AI/claude-code/2.1.20/24.03-lts-sp4/Dockerfile`: 新增 `ARG CURL_USER_AGENT` 定义浏览器 User-Agent 字符串，并在 `curl` 命令中添加 `-H "User-Agent: ${CURL_USER_AGENT}"` 参数。

## 修复逻辑
CI 分析报告方向 1（置信度: 中）指出 `claude.ai/install.sh` 可能对非浏览器 User-Agent 有限制。经测试，该 URL 当前可正常访问（返回 302 重定向至 `https://downloads.claude.ai/claude-code-releases/bootstrap.sh`），但 CI 环境中 curl 默认请求头被拒绝。通过在 curl 命令中添加 Chrome 浏览器 User-Agent 请求头，使请求模拟浏览器行为，提高服务器接受概率。

## 潜在风险
- 如果未来 Anthropic 变更 `claude.ai/install.sh` 的 URL，可能需要同步更新 `CLAUDE_INSTALL_SCRIPT` 参数。
- 同仓库 `AI/claude-code/2.1.20/24.03-lts-sp3/Dockerfile` 使用相同 URL 但未添加 User-Agent，如果 sp3 构建也出现 403，需要同步修复（当前未被要求修改）。