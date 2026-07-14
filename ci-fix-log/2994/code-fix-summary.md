# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施层面的瞬时故障（BuildKit builder `euler_builder_20260709_224657` 在 `dnf install` 下载元数据阶段被 CI 基础设施主动终止，`graceful_stop` goaway 帧），与 PR 新增的 Dockerfile 内容无关。

## 修改的文件
无

## 修复逻辑
分析报告判定失败类型为 `infra-error`，根因为 BuildKit 构建器被 CI 基础设施终止，而非代码问题。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，所安装的包名均为 openEuler 仓库标准包。按照修复原则，infra-error 无需代码修改，应通过重新触发 CI 构建（如 `/retest`）解决。

## 潜在风险
无