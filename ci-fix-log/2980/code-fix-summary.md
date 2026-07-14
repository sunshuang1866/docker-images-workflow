# 修复摘要

## 修复的问题
未修改任何代码。CI 失败的原因是 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议间歇性错误（Curl error 92, INTERNAL_ERROR），属于 `infra-error`（CI 基础设施问题），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认失败类型为 `infra-error`，根因是 `repo.****.org` 镜像站在发送 `gcc-c++`、`cmake-data` 等大文件时 HTTP/2 流异常中断（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`）。PR 新增的 Dockerfile 中 `dnf install` 命令完全合法，所有列出的软件包均正常存在于仓库中。日志中 `cmake-data` 和 `git-core` 在遭遇同样错误后重试成功，进一步佐证服务端不稳定是间歇性的。

根据任务规范，`infra-error` 场景下不应强行修改代码。需等待 openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 服务恢复后重新触发 CI 构建即可通过。

## 潜在风险
无