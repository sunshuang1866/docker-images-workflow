# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），BuildKit builder 容器在 bootstrap 阶段崩溃（`Could not find the file / in container`），与 PR 提交的 Dockerfile 及元数据文件无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：失败发生在 `[internal] booting buildkit` 阶段，即 Docker BuildKit 守护进程层，尚未进入任何 Dockerfile 的构建步骤。错误信息 `Error response from daemon: Could not find the file / in container` 表明 runner 节点 `ecs-build-docker-x86-hk` 上的 Docker daemon / BuildKit builder 实例启动异常，可能由磁盘空间不足、overlay2 存储驱动故障或 `moby/buildkit:buildx-stable-1` 镜像拉取不完整导致。属于 CI 基础设施瞬时性故障，建议重试 CI 任务。

## 潜在风险
无