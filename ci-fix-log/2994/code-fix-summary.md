# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施层面的瞬态故障（BuildKit builder 实例意外终止），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`。构建在 Dockerfile 的 `dnf install` 步骤中失败，错误为 `ERROR: no builder "euler_builder_20260709_224657" found`，原因是 BuildKit builder 实例被 CI 基础设施意外回收（`graceful_stop` + `NO_ERROR` goaway）。PR 新增的 Dockerfile 语法和内容没有问题。建议重新触发 CI 运行即可。

## 潜在风险
无