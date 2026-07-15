# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施瞬时故障（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被外部终止（`graceful_stop`），与 PR 代码变更无关。

## 修改的文件
无。PR 新增的 Dockerfile 及元数据文件（`Dockerfile`、`README.md`、`image-info.yml`、`meta.yml`）均无语法或逻辑错误。

## 修复逻辑
分析报告明确指出此为 infra-error，根因是 BuildKit builder 节点因外部原因（如节点池调度回收、资源预占释放等）被主动关闭，导致构建连接断开。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据，`dnf install` 阶段失败发生在基础设施层，与代码变更无因果关联。

**正确操作**：重新触发 CI pipeline 构建即可。若多次重试均在同一位置失败，则需排查 builder 节点资源（内存/磁盘）。

## 潜在风险
无