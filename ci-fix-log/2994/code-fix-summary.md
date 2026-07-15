# 修复摘要

## 修复的问题
CI 基础设施瞬态故障：BuildKit builder 节点在 `dnf install` 阶段被优雅关闭（graceful_stop），导致构建中断。无需修改 PR 代码。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 分析报告明确判定为 `infra-error`，置信度高。错误发生在 Docker 构建的 `dnf install` 阶段，BuildKit builder 实例 `euler_builder_20260709_224657` 被中途关闭，gRPC 连接断开导致失败。这与 PR #2994 中新增的 scann 1.4.2 openEuler 24.03-lts-sp4 Dockerfile 及相关元数据文件无关。重新触发 CI 流水线即可。

## 潜在风险
无