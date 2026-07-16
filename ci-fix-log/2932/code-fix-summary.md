# 修复摘要

## 修复的问题
CI 基础设施故障，无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败为 `infra-error`，错误发生在 BuildKit builder 容器启动阶段（`moby/buildkit:buildx-stable-1` 容器创建时 containerd 报错 `Could not find the file / in container`），早于 Dockerfile 被解析或执行的任何步骤。该错误与 PR #2932 的代码变更无关（PR 仅新增 glibc 2.42 的 Dockerfile 及更新元数据文件）。此类问题为 Docker daemon / containerd 在 CI runner 节点 `ecs-build-docker-x86-hk` 上的瞬时异常，可通过 CI 重试恢复。

## 潜在风险
无。