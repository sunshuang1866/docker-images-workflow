# 修复摘要

## 修复的问题
无代码修复。CI 失败为基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无。此 PR 的所有代码变更（`Others/glibc/2.42/24.03-lts-sp4/Dockerfile`、`README.md`、`doc/image-info.yml`、`meta.yml`）均无需修改。

## 修复逻辑
CI 失败发生在 Docker BuildKit bootstrap 阶段（`booting buildkit`），在 CI 构建节点 `ecs-build-docker-x86-hk` 上 Docker daemon 创建 BuildKit 容器时报错 `Could not find the file /`，这是容器根文件系统元数据异常导致的基础设施瞬时故障，发生在任何 Dockerfile 指令被处理之前。PR 的前置检查步骤（依赖安装、仓库克隆、diff 识别、镜像规范校验）均成功通过，确认代码变更本身没有问题。修复方向应为触发 CI 重试或清理 CI 节点 Docker 存储，无需修改代码。

## 潜在风险
无