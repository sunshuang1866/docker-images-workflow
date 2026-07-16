# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 BuildKit builder 实例 (`euler_builder_20260709_224657`) 在 `dnf install` 过程中被意外优雅关闭（`graceful_stop`），导致 gRPC 连接中断，属于 CI 基础设施瞬态故障（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告定性为 infra-error，根因是 BuildKit builder 连接中断 (`rpc error: code = Unavailable desc = closing transport`)，非代码或配置错误。PR 仅新增了标准 Dockerfile（安装依赖→编译 Python→pip 安装 scann），无语法错误或逻辑问题。建议重试 CI 触发重新构建即可。

## 潜在风险
无