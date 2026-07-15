# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施层面的网络问题（HTTP/2 协议流错误），与 PR 代码变更无关。

## 修改的文件
无（infra-error，无需修改任何代码）

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`。`dnf install` 从 `repo.****.org`（openEuler 24.03-LTS-SP4 镜像仓库）下载 RPM 包时，curl 遇到 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`）。`cmake-data` 和 `git-core` 经重试后成功下载，仅 `gcc-c++` 多次重试仍失败，触发构建终止。

此问题由 CI 镜像仓库的网络瞬态故障导致，PR 新增的 Dockerfile 中 `dnf install` 语法正确、依赖包名称完整，代码本身没有问题。

**建议操作**：重新触发 CI 构建，HTTP/2 流错误通常为重试即可解决的瞬态网络问题。

## 潜在风险
无