# 修复摘要

## 修复的问题
无需代码修改。本次 CI 失败为基础设施问题（infra-error）：CI 构建环境无法连接 `archive.apache.org`，且 CI 可能存在 URL 重写机制将 `dlcdn.apache.org` 的请求也定向到 `archive.apache.org`。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告将本次失败归类为 `infra-error`，根因是 CI runner（aarch64）无法与 `archive.apache.org:443` 建立 TCP 连接（curl 超时 exit code 28），而非 Dockerfile 代码逻辑错误。虽然可通过将下载源切换到华为云或清华镜像站来绕过（参考历史案例 PR #3101/#3077 等），但更合理的修复应在 CI 基础设施层面解决网络可达性问题或修正 URL 重写逻辑。根据任务约束——infra-error 不应通过修改代码来强行绕过——本次不做代码变更。

## 潜在风险
无