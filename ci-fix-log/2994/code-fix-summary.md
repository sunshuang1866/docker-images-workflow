# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被优雅关闭（`graceful_stop`），导致 buildx 客户端与 builder 之间的 gRPC 连接断开。与 Dockerfile 或任何 PR 代码变更无关。

## 修改的文件
无。本次失败无需修改任何代码文件。

## 修复逻辑
根据 CI 失败分析报告，失败发生在 `dnf install` 下载元数据过程中，BuildKit builder 被意外终止，属于 CI 基础设施的偶发性问题（可能由节点资源回收、调度超时、builder 健康检查失败等触发）。PR 新增的 Dockerfile 语法和包名均无错误。唯一有效的修复方式是重新触发 CI 构建。

## 潜在风险
无