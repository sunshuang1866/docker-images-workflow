# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施错误（infra-error）：BuildKit builder `euler_builder_20260709_224657` 在执行 `dnf install` 下载 openEuler 仓库元数据时被优雅终止（`graceful_stop`），与 PR #2994 新增的代码变更无关。

## 修改的文件
- 无（infra-error，无需代码修改）

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因为 BuildKit 构建器实例被意外终止（连接超时/builder 回收），发生在 `dnf install` 下载仓库元数据阶段（第 2/4 步），尚未到达 scann 软件本身的构建步骤。PR 仅新增 Dockerfile 及元数据文件，属于正常的镜像配置新增，不存在代码层面问题。建议重新触发 CI 运行即可。

## 潜在风险
无