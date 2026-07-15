# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 BuildKit 基础设施瞬时故障（builder 容器被 `graceful_stop`，连接断开），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告将本次失败归类为 `infra-error`，置信度中。失败发生在 `RUN dnf install` 阶段下载 openEuler 24.03-lts-sp4 仓库元数据过程中，BuildKit builder 容器 (`euler_builder_20260709_224657`) 被服务端主动发送 GOAWAY `graceful_stop` 关闭，导致 transport 连接断裂（`error reading from server: EOF`）。Dockerfile 本身的指令无任何语法或逻辑问题。

根据修复规范，`infra-error` 类型的 CI 失败无需修改代码，不应强行改动源文件。建议重新触发 CI 流水线（Re-run），多数情况下 builder 资源恢复正常后构建可顺利完成。

## 潜在风险
无。未修改任何文件。