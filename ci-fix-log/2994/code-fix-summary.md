# 修复摘要

## 修复的问题
无需代码修改。此次 CI 失败为基础设施错误（infra-error），BuildKit 构建器实例在 `dnf install` 下载仓库元数据阶段崩溃（`EOF` + `graceful_stop`），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确判定失败类型为 `infra-error`，置信度高。构建器实例 `euler_builder_20260709_224657` 在执行 `RUN dnf install` 约 38 秒时意外终止（连接丢失、graceful_stop），此时尚未执行到任何与 PR 代码逻辑相关的步骤。PR 新增的 Dockerfile 语法正确，`dnf install` 参数合法，无需任何代码修改。

**建议操作**：重新触发 CI 构建即可。若重试后仍然失败，需排查 CI 基础设施侧的 BuildKit 守护进程日志及 runner 资源配额。

## 潜在风险
无