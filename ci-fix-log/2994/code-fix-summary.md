# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施错误（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 仓库元数据期间被外部信号终止（graceful_stop），导致构建连接断开。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告明确判定此失败为 **infra-error**，与 PR 变更无关。PR 仅新增了一个标准 Dockerfile 及配套元数据文件，构建在执行第一步 `dnf install`（Step 7/4）时 BuildKit daemon 被外部调度器主动发送 GOAWAY 信号关停（`graceful_stop` + `code: NO_ERROR`），属于 CI runner / BuildKit builder 基础设施层面的问题。

- 日志显示 Docker 构建在 `dnf install` 下载元数据到约 38.59s 时连接断开
- `graceful_stop` 表明 builder 是外部主动终止，非自身崩溃
- 后续 `no builder "euler_builder_20260709_224657" found` 确认 builder 已被清理

**按规范要求，infra-error 不进行代码修改。** 建议触发 CI 重试（re-run）。

## 潜在风险
无