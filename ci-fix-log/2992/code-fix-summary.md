# 修复摘要

## 修复的问题
CI 基础设施故障：openEuler 24.03-LTS-SP4 RPM 仓库 HTTP/2 传输层异常，无需代码修改。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败根因为 `repo.****.org`（openEuler 24.03-LTS-SP4 软件包仓库）在构建时出现 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer — INTERNAL_ERROR），导致 `dnf install` 下载 RPM 包失败。此错误与 PR #2992 的代码变更无关，Dockerfile 中 `dnf install` 命令语法和包名均正确合法。属于仓库侧临时服务端故障，Code Fixer 无需执行任何代码修改，触发 CI re-run 即可。

## 潜在风险
无。若重试后仍失败，需由基础设施团队排查 `repo.****.org` 的 HTTP/2 协议栈兼容性问题。