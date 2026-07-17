# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 BuildKit 基础设施偶发故障（`[internal] booting buildkit` 阶段 builder 容器创建后根文件系统不可访问），与 PR 代码变更无关。

## 修改的文件
无。本次为 infra-error，不需要修改任何源文件。

## 修复逻辑
CI 日志明确显示：
- 失败发生在 BuildKit builder 容器初始化阶段（`[internal] booting buildkit`），早于任何 Dockerfile 构建步骤的执行
- 没有任何来自 Dockerfile 内 `RUN` 指令的错误输出
- 直接错误为 `Error response from daemon: Could not find the file / in container buildx_buildkit_euler_builder_20260709_2057000`，属于 Docker daemon 存储驱动 / 运行时层面的基础设施问题

建议操作：重新触发 CI 构建。若重试后仍然复现，需排查构建节点上的 Docker 存储驱动或 buildx builder 实例状态。

## 潜在风险
无（未修改任何代码）。