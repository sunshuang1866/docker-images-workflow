# 修复摘要

## 修复的问题
CI 构建失败为基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。该失败为 BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据时被基础设施层面终止（`graceful_stop`），与 PR 的代码变更无关。

## 修复逻辑
CI 分析报告已明确指出：
- 失败类型为 `infra-error`，根因是 BuildKit 构建器因超时或资源回收被终止
- PR 仅新增了 scann 1.4.2 的 Dockerfile 及配套元数据文件，Dockerfile 中 `dnf install` 命令语法正确、包名有效
- PR 的代码变更不会触发 Builder 生命周期管理问题
- 建议重新触发 CI 构建（retry）即可通过

按照流程规范，infra-error 不应强行修改代码。

## 潜在风险
无。