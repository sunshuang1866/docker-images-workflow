# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施故障（BuildKit 构建器异常终止），与 PR 代码变更无关。

## 修改的文件
无（零代码修改）

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，置信度高。根因是 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 阶段被主动发送 `graceful_stop` 信号并断开连接，导致 Docker build 失败。PR 仅新增了标准的 scann 应用镜像 Dockerfile 及元数据文件，内容无任何语法或逻辑问题。该失败与 PR 代码变更无关，属于 CI 构建节点的资源/超时问题。

**建议操作**：在 CI 侧重新触发构建（retry），通常重试即可通过。若持续失败，需排查构建节点资源状况（内存/磁盘/OOM）或 BuildKit 构建器 TTL 配置。

## 潜在风险
无