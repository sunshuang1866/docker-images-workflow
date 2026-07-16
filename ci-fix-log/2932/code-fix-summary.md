# 修复摘要

## 修复的问题
CI 构建在 BuildKit 初始化阶段失败（`Could not find the file / in container`），属于 Docker 容器运行时基础设施故障（infra-error），**无需修改任何源代码**。

## 修改的文件
无。本次 CI 失败与 PR #2932 的代码变更无关，发生在 BuildKit 启动阶段，早于任何 Dockerfile 指令的执行。

## 修复逻辑
- **根因**：构建节点 `ecs-build-docker-x86-hk` 上的 Docker 守护进程或 containerd 存储驱动出现瞬态异常，导致 `docker-container` 驱动模式下 BuildKit 容器创建失败。
- **修复方向**：重新触发 CI 构建。该故障为 Docker 容器运行时的瞬态基础设施问题，通常重试即可恢复。若重试后仍失败，需排查构建节点上的 Docker 守护进程状态及 containerd 存储驱动（overlay2）是否正常。

## 潜在风险
无（无代码修改）。