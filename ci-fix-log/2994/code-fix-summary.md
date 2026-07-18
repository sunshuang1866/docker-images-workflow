# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施问题（infra-error）：Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 阶段被优雅关闭（graceful_stop），gRPC 连接断开导致构建失败。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告明确指出这是 infra-error，失败发生在 BuildKit builder 节点层面（connection error / graceful_stop），与 PR 代码变更无关。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套元数据文件，构建在 `dnf install` 安装基础系统包阶段即失败，尚未进入任何 PR 特定的构建逻辑。建议重试 CI 流水线。

## 潜在风险
无。