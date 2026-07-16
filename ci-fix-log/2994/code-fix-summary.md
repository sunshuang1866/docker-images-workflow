# 修复摘要

## 修复的问题
CI 基础设施瞬态故障（BuildKit builder 被外部调度系统终止），与 PR 代码变更无关，无需修改代码。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`。构建在 `dnf install` 执行到 38 秒时因 BuildKit daemon（`euler_builder_20260709_224657`）被外部调度系统优雅终止（`graceful_stop`）而中断，导致 gRPC 连接断开。错误发生在基础镜像已成功拉取、第一个 RUN 指令执行期间，与 Dockerfile 内容完全无关。PR 新增的 Dockerfile 仅包含标准的 `dnf install` 编译依赖和源码编译步骤，没有异常操作。按照修复规范，`infra-error` 类别的失败无需对源码做任何修改，仅需重新触发 CI 构建即可验证。

## 潜在风险
无