# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。BuildKit 构建器实例在执行 `dnf install` 时被优雅终止（`graceful_stop`），导致构建中断。

## 修改的文件
无代码需要修改。

## 修复逻辑
CI 失败分析报告明确指出：失败类型为 `infra-error`，根因是 BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 执行期间（已运行 38 秒）被优雅终止，与 PR 代码变更无关。PR 仅新增了标准的 Dockerfile（基于 openEuler 24.03-LTS-SP4 安装 scann 1.4.2）及配套文档更新，Dockerfile 语法和内容均无问题。重新触发 CI 构建即可恢复。

## 潜在风险
无