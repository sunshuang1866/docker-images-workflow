# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施故障（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被外部关闭（graceful_stop），导致 gRPC 连接中断，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
根据 CI 分析报告，失败发生在 Docker 构建的基础设施层面，而非代码层面。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的标准 Dockerfile 及配套元数据文件，构建在 `dnf install` 步骤中因 builder 实例被调度系统/运维操作关闭而中断。该步骤内容与相邻镜像（24.03-lts-sp3）完全一致，`dnf` 本身已成功启动并正在同步元数据，失败纯因 builder 被外部关闭。

**建议操作**：触发该 PR 的 CI 重新构建（retry）。若多次重试仍出现同类问题，需由 CI 运维排查 builder 节点的资源回收/节点轮换策略。

## 潜在风险
无