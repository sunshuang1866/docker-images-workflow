# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。PR 代码变更正确，无需修改。

## 修复逻辑
CI 失败分析报告确认此为 infra-error：BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据阶段被服务端主动发送 `graceful_stop` goaway 信号后关闭，导致 gRPC 连接中断（`error reading from server: EOF`）。该失败属于 CI 基础设施的偶发性故障（构建器被服务端主动回收），与 PR 代码变更无关。Dockerfile 中 `dnf install` 命令参数正确，包名均合法。

**修复方向：触发 CI 重试（retry）即可。**

## 潜在风险
无。未修改任何代码，不引入任何风险。