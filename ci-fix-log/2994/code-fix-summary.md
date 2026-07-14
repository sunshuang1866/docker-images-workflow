# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施临时故障（BuildKit builder 被 `graceful_stop`，导致 `dnf install` 步骤中断），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：
- 失败发生在 BuildKit builder `euler_builder_20260709_224657` 执行 `dnf install` 时被意外终止（`graceful_stop`），gRPC 连接断开（`EOF`）
- PR 新增的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 内容正确，基础镜像拉取成功（`#6 DONE 2.9s`），`dnf install` 步骤本身无语法或逻辑错误
- 此为 `infra-error`，应通过 CI 平台重试机制解决

**解决方式**：重新触发该 PR 的 CI pipeline 即可。

## 潜在风险
无