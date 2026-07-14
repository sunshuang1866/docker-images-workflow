# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 BuildKit builder 实例意外终止（infra-error），与 PR 代码变更无关。

## 修改的文件
无。此失败为 CI 基础设施问题，不涉及任何代码文件修改。

## 修复逻辑
CI 日志显示 BuildKit builder 实例 `euler_builder_20260709_224657` 在 Dockerfile Step 2/4（`RUN dnf install ...`）执行期间被 `graceful_stop` 终止，导致 gRPC 连接断开。该步骤仅在下载系统软件包仓库元数据，尚未执行任何与 scann 或 Python 编译相关的操作。Dockerfile 内容无异常，失败属于 CI 宿主机资源紧张或 builder 被 scheduler 回收导致的临时性基础设施故障。

**修复方向**：重新触发 CI 构建即可。

## 潜在风险
无。