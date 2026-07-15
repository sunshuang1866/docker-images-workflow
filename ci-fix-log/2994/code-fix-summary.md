# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。BuildKit 构建器 `euler_builder_20260709_224657` 在 Dockerfile 第 2/4 步（`dnf install` 下载 OS 元数据阶段）被 CI 基础设施发送 `graceful_stop` 信号终止，与 PR 代码逻辑无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认该失败属于基础设施问题（infra-error），置信度高。失败原因为 BuildKit 构建器实例被意外回收/终止（`rpc error: code = Unavailable`、`graceful_stop`、`no builder found`），发生在 `dnf install` 下载仓库元数据的中途，非 PR 代码问题。PR 变更仅新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件，Dockerfile 内容为标准构建步骤，无语法或逻辑错误。应通过重新触发 CI job 重试。

## 潜在风险
无