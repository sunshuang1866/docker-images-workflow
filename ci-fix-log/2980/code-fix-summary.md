# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 openEuler 24.03-LTS-SP4 仓库镜像站在 HTTP/2 传输层出现临时性网络错误（Curl error 92: INTERNAL_ERROR），属于 CI 基础设施问题，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认为 `infra-error`：构建过程中 `gcc-c++` 包下载时遇到 HTTP/2 流中断错误，`cmake-data` 和 `git-core` 重试后成功，但 `gcc-c++` 在耗尽所有镜像站后仍然失败。PR 新增的 Dockerfile 中 `dnf install` 的包名和语法均正确，与已有 `24.03-lts-sp3` 版本使用相同模式。建议直接触发 CI 重试（re-run），无需修改任何代码。

## 潜在风险
无