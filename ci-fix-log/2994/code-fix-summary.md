# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（BuildKit builder 进程崩溃），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`，根因是 BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载阶段被优雅关闭（`graceful_stop`），导致 gRPC 连接断开。PR #2994 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套文档，Dockerfile 内容、基础镜像拉取、依赖安装步骤均正常运行，失败与代码变更无关。按照修复原则，infra-error 不应强行修改代码。

**建议操作**: 重试 CI job，若重试后通过则确认是偶发基础设施波动。

## 潜在风险
无