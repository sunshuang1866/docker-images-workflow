# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施级别故障（BuildKit builder 实例意外终止），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此为 `infra-error`：BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 阶段被 `graceful_stop` 意外终止，导致 gRPC 连接中断、构建失败。本次 PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），这些纯文本/配置变更不会导致 BuildKit builder 实例崩溃。建议直接重新触发 CI 构建。

## 潜在风险
无