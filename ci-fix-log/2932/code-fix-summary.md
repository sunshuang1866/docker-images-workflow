# 修复摘要

## 修复的问题
CI 基础设施故障（infra-error），与 PR 代码无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 Docker BuildKit 容器启动阶段（`[internal] booting buildkit`），报错 `Could not find the file / in container buildx_buildkit_euler_builder_20260709_2057000`。此时构建尚未进入 PR 的 Dockerfile 中的任何 `RUN`、`COPY` 等指令，属于构建节点 `ecs-build-docker-x86-hk` 上 Docker daemon 或 buildx builder 实例的基础设施问题。

**建议操作**：重新触发 CI 构建（re-trigger）。若持续失败，需运维排查构建节点上的 Docker daemon 状态、buildx builder 残留实例（`docker buildx rm` 清理）及磁盘/inode 资源。

## 潜在风险
无