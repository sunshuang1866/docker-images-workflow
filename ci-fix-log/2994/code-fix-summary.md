# 修复摘要

## 修复的问题
CI 基础设施临时故障（infra-error）：BuildKit builder 实例在构建过程中被底层平台终止，导致 Docker build 连接中断。与 PR 代码变更无关。

## 修改的文件
无（无需修改任何源代码）

## 修复逻辑
CI 失败分析报告认定此次失败为 **infra-error**，置信度**高**。失败发生在 Docker build 第 2/4 步（`RUN dnf install -y ...`）下载仓库元数据阶段，BuildKit builder（`euler_builder_20260709_224657`）被基础设施层优雅终止（goaway `graceful_stop`），客户端连接断开。

PR #2994 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 和 3 个元数据文件的更新，不涉及任何可能影响 BuildKit 基础设施的行为。此失败属于 CI runner 节点资源回收或 builder 超时自动清理等临时问题。

**修复方向：无需修改代码，触发 CI 重试即可。**

## 潜在风险
无