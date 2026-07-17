# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中被优雅终止（`graceful_stop`），属于 CI 基础设施不稳定导致的一次性故障，与本次 PR 的代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
分析报告确认：构建失败发生在 `dnf install` 系统包安装阶段（下载 openEuler 仓库元数据时），尚未执行到 Dockerfile 中任何项目特定的 `RUN` 指令。失败的直接原因是 BuildKit 构建器异常终止导致 gRPC 连接断开。PR #2994 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据文件，均为常规的镜像版本新增操作，与构建器故障无关联。建议重新触发 CI pipeline 重试构建。

## 潜在风险
无