# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 BuildKit 基础设施故障（BuildKit 构建器容器创建后 Docker daemon 内部状态异常，报错 "Could not find the file /"），发生在 Dockerfile 任何指令执行之前，与 PR 代码变更无关。

## 修改的文件
无。PR 涉及的源代码文件（Dockerfile、README.md、image-info.yml、meta.yml）均无问题，无需修改。

## 修复逻辑
CI 失败类型为 `infra-error`，根因为 Docker daemon/BuildKit 在 CI runner 上的瞬态故障。错误发生在 `[internal] booting buildkit` 阶段，此时 Dockerfile 尚未被解析或执行。建议重试 CI job 即可恢复；若持续复现，需运维检查 CI runner `ecs-build-docker-x86-hk` 的 Docker daemon 健康状态、磁盘空间及 BuildKit 缓存。

## 潜在风险
无