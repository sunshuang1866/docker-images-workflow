# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error），BuildKit builder 实例在构建过程中被异常优雅关闭（graceful_stop），与 PR 代码变更无关。

## 修改的文件
无。未修改任何文件。

## 修复逻辑
CI 失败分析报告确认：失败类型为 `infra-error`，根本原因是 BuildKit builder `euler_builder_20260709_224657` 在 `dnf install` 阶段被外部触发优雅关闭，导致 gRPC 连接断开。该 PR 仅新增 scann 的 openEuler 24.03-LTS-SP4 支持（Dockerfile、README、meta.yml、image-info.yml），Dockerfile 中的 `dnf install` 命令是该仓库的标准写法，不存在语法或逻辑错误。建议重新触发 CI 流水线。

## 潜在风险
无。