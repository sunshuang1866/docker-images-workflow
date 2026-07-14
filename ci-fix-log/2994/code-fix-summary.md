# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 BuildKit 基础设施故障（`graceful_stop`），与 PR 代码变更无关。

## 修改的文件
无（infra-error，不需要代码修改）

## 修复逻辑
CI 构建在执行 `dnf install` 下载系统包时（耗时约 39 秒），BuildKit daemon 发出 `graceful_stop`（GOAWAY），主动终止了构建会话，导致 `no builder found` 和 `EOF` 错误。这是 CI runner 节点上 BuildKit daemon 被外部信号终止导致的偶发性基础设施问题，与 PR 新增的 Dockerfile 及其内容无关。Dockerfile 经检查无语法或逻辑错误。

建议重新触发 CI 构建（retry），大概率可通过。如重试后仍失败，需排查 CI runner 节点上 BuildKit daemon 的运行状态。

## 潜在风险
无