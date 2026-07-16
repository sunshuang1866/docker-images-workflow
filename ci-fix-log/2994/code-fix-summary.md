# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施错误（infra-error）：Docker buildx builder 实例在构建过程中被优雅终止（graceful_stop），与 PR 代码变更无关。

## 修改的文件
无。未对任何文件进行修改。

## 修复逻辑
CI 分析报告明确指出：
- 失败类型为 `infra-error`，置信度：高
- 根因：builder 实例 `euler_builder_20260709_224657` 被 CI 调度系统/宿主机主动回收，gRPC 连接断开
- 失败发生在 `dnf install` 基础依赖安装阶段（步骤 2/4），此时尚未执行到与 scann 直接相关的构建步骤
- PR 变更内容（新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及元数据文件）与构建失败无关联

修复方向：重新触发 CI 构建即可，无需代码修改。

## 潜在风险
无