# 修复摘要

## 修复的问题
无代码修改 — 此为 CI 基础设施故障（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生 Docker BuildKit 引导阶段（`[internal] booting buildkit`），在从 `moby/buildkit:buildx-stable-1` 镜像创建 builder 容器时，Docker daemon 报错 `Could not find the file / in container`。此时尚未进入 PR 所提交的 Dockerfile 构建步骤（未执行任何 RUN、COPY 等指令），PR 中的 4 个文件变更（Dockerfile、README.md、image-info.yml、meta.yml）均不涉及 CI 基础设施或 Docker daemon 配置。

因此无需修改任何 PR 代码。应通过以下 CI 基础设施操作解决：
- 检查 CI runner 节点 `ecs-build-docker-x86-hk` 上 Docker daemon 存储驱动和磁盘状态
- 清理残留的 buildkit 容器或重启 Docker daemon
- 必要时重新拉取 `moby/buildkit:buildx-stable-1` 镜像后重试 CI

## 潜在风险
无 — 未修改任何代码，无引入新问题的风险。