# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error）：BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载系统包过程中被外部终止（gRPC `graceful_stop`），导致构建连接中断。

## 修改的文件
无

## 修复逻辑
该失败与 PR 的 Dockerfile 或元数据变更无关。`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 是合法且常见的依赖安装命令。失败发生在 `dnf` 下载系统元数据耗时约 38 秒后，BuildKit builder 被 CI 基础设施意外终止，属于纯粹的 CI 基础设施问题。建议重新触发 CI 构建（retry），大概率可通过。

## 潜在风险
无