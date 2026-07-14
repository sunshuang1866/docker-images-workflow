# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 Docker daemon / buildx 基础设施瞬时故障（BuildKit builder 容器创建失败），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出失败类型为 `infra-error`，根因是 Docker daemon 在初始化 BuildKit builder 容器时出现 `Could not find the file / in container` 错误，发生在 Dockerfile 构建真正开始之前。该错误属于 CI runner（`ecs-build-docker-x86-hk`）上的瞬时基础设施故障，与 PR #2932 新增的 glibc Dockerfile 及 README/meta/image-info 文档更新无关。修复方向为：重试 CI 构建或排查 runner 节点 Docker daemon 状态。

## 潜在风险
无