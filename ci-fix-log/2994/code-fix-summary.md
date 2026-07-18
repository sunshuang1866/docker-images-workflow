# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施瞬时故障（infra-error），BuildKit builder 实例被 CI 基础设施层主动优雅终止。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败分析报告明确诊断为 `infra-error`，置信度 **高**。根因为 BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据时（约 38.59 秒处）被 CI 基础设施端主动优雅终止（`goaway: code: NO_ERROR, debug data: "graceful_stop"`）。该失败发生在 `dnf` 下载阶段，尚未执行到任何可能由 Dockerfile 内容引起的错误，与 PR 代码变更无关。

**修复方向**：直接重新触发 CI 构建。若问题持续复现，需要 CI 运维团队排查 BuildKit builder 的生命周期管理策略。

## 潜在风险
无