# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 **infra-error**：Docker BuildKit 容器在 CI runner 节点 `ecs-build-docker-x86-hk` 上启动时，Docker daemon 报告 `Could not find the file / in container`，属于 overlay2/containerd 存储层瞬态故障。PR #2932 的代码变更（Dockerfile 及元数据文件）与此次失败无关，镜像构建步骤从未被调用。

## 修改的文件
无（infra-error，无需修改任何源代码）。

## 修复逻辑
CI 失败发生在 `[internal] booting buildkit` 阶段，此时尚未执行任何 PR 引入的 Dockerfile 或构建逻辑。根因是 CI runner 节点上 Docker daemon 的存储子系统异常，属于基础设施问题，与代码无关。建议操作：在 CI 中重新触发该 job（retry），让 buildx 在新的 Docker daemon 状态下重新创建 BuildKit 容器。

## 潜在风险
无（未修改任何代码）。