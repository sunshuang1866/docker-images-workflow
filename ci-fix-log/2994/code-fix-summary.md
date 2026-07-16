# 修复摘要

## 修复的问题
无需代码修复。此 CI 失败是基础设施问题（infra-error），BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建执行 `dnf install` 约 38 秒时被优雅关闭（`graceful_stop`），导致构建连接断开（EOF），与 PR 代码变更无关。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`，根因是 CI 基础设施层面的 BuildKit 构建器生命周期管理问题（构建器在构建进行中被意外终止），而非 PR 代码问题。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据，Dockerfile 语法和逻辑均正常。应重新触发 CI 流水线（re-run）重试构建。

## 潜在风险
无。如果该问题持续复现，需排查 BuildKit builder（`docker-container` driver）的运行环境稳定性（如 runner 节点资源耗尽、OOM、构建器超时回收策略等）。