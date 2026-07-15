# 修复摘要

## 修复的问题
无代码修改。此为 CI 基础设施故障（infra-error），BuildKit 构建器实例被服务端 `graceful_stop` 回收导致 RPC 连接中断。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 Docker 构建步骤 `[2/4]` 的 `dnf install` 下载 OS 元数据阶段。BuildKit 构建器实例 `euler_builder_20260709_224657` 被基础设施层主动关闭（GOAWAY frame，debug data:`graceful_stop`），导致 BuildKit 客户端 RPC 连接中断。此故障与 PR #2994 的代码变更无关，Dockerfile 中的 `dnf install` 命令语法正确。建议重新触发 CI 构建（retry）即可通过。

## 潜在风险
无