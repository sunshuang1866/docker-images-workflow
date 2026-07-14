# 修复摘要

## 修复的问题
无代码修改 — 本次 CI 失败属于 **infra-error**（CI 基础设施问题），与 PR #2995 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败发生在 `[Check]` 校验阶段，由 eulerpublisher 内置的 `bwa_test.sh` 测试脚本的 Windows 风格 CRLF 换行符导致。该脚本的 shebang 行 `#!/bin/sh` 末尾带有 `\r`，内核将其解析为 `/bin/sh\r`，报 "bad interpreter: No such file or directory"。

本次 PR 的 Docker 镜像构建和推送均完全成功（日志中 `#7 DONE`、`[Build] finished`、`[Push] finished` 均可证实），产出的镜像已成功推送到 registry。此问题与 PR 变更的 Dockerfile 及元数据文件**完全无关**，属于 CI 基础设施（eulerpublisher 测试套件）的预存缺陷。

**无需修改本 PR 的任何代码文件。** 此问题需要由 CI 基础设施维护者在 eulerpublisher 包或 CI runner 环境中修复（例如对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 去除 CRLF 换行符）。

## 潜在风险
无