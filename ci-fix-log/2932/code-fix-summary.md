# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`（基础设施错误），错误发生在 Docker BuildKit builder 容器引导阶段（`Could not find the file /`），Dockerfile 尚未被解析或执行，与 PR #2932 的代码变更无关。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，错误 `Error response from daemon: Could not find the file /` 发生在 `[internal] booting buildkit` 阶段，属于 CI runner 节点 `ecs-build-docker-x86-hk` 上 Docker daemon / BuildKit 的间歇性基础设施故障。PR 变更的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）在语法和结构上均无异常，不会导致该类型错误。

**建议操作**：重新触发 CI 流水线。若多次重试仍失败，需排查 CI runner 节点上的 Docker daemon 状态（磁盘空间、inode 耗尽、残留 buildx builder 实例等）。

## 潜在风险
无