# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 BuildKit builder 基础设施瞬时故障（graceful_stop 信号导致构建中断），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被 `graceful_stop` 信号终止，导致 gRPC 传输层中断（`closing transport due to: connection error`）。PR 变更仅新增标准 scann Dockerfile 及相关元数据文件，构建失败发生在基础设施操作阶段，与代码逻辑完全无关。建议重新触发 CI 构建流水线。

## 潜在风险
无