# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被服务端主动发送 `graceful_stop` 信号关闭，导致 gRPC 连接中断。

## 修改的文件
无（未修改任何源代码文件）

## 修复逻辑
CI 分析报告确认本次失败与 PR #2994 的代码变更无关。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 等 4 个常规镜像版本文件，构建在执行 `dnf install` 阶段时，BuildKit builder 因 CI 集群调度/资源回收策略被提前销毁。这是 CI 基础设施的偶发性问题，重新触发 CI 构建即可。

## 潜在风险
无