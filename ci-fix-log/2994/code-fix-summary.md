# 修复摘要

## 修复的问题
CI 基础设施故障（BuildKit 构建器被 `graceful_stop` 信号意外终止），与 PR 代码变更无关。无需代码修改。

## 修改的文件
无（infra-error，不涉及代码修改）

## 修复逻辑
CI 在 Docker 构建步骤 `[2/4] RUN dnf install ...` 的 dnf 下载 OS 元数据阶段，BuildKit 构建器实例 `euler_builder_20260709_224657` 被 CI 管理面发送 `graceful_stop` 信号回收，导致 RPC 连接断开（EOF），构建中断。本次 PR (#2994) 仅新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套配置文件，Dockerfile 内容为标准模式，与已有版本结构一致，不存在能导致构建器崩溃的代码。故障点在 `dnf install` 下载阶段（未进入任何 PR 引入的定制逻辑），属 CI 基础设施偶发问题。

## 潜在风险
无。建议重新触发 CI 流水线（re-run）重试；若多次重试均在同一阶段失败，需排查 CI 构建节点资源（内存、磁盘）是否不足。