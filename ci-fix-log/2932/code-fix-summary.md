# 修复摘要

## 修复的问题
CI 基础设施工效故障：Docker buildx BuildKit 容器创建时报错 `Could not find the file /`，此为 CI 构建节点 `ecs-build-docker-x86-hk` 上 Docker daemon 的临时性异常，与 PR 代码变更无关。

## 修改的文件
无。该失败属于 `infra-error`，PR 代码无需任何修改。

## 修复逻辑
CI 日志显示错误发生在 BuildKit `booting buildkit` 阶段——此时尚未进入 Dockerfile 解析（`FROM` / `RUN` 指令执行），PR 新增的 Dockerfile 内容尚未被评估。该错误是构建节点上 Docker 运行时的临时性基础设施故障（可能由 daemon 状态异常、cgroup 资源不足或 buildx 残留实例导致）。建议重新触发 CI 构建以确认是否为临时性故障；若重试后仍失败，需排查构建节点的 Docker daemon 和 buildx 状态。

## 潜在风险
无