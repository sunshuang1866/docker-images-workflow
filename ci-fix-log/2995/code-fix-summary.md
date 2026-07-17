# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施错误（infra-error），与本次 PR 代码变更无关。

## 修改的文件
无。本次失败根因在于 eulerpublisher 包中的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 shebang 行被解释为 `/bin/sh^M`，系统找不到解释器而失败。

## 修复逻辑
分析报告确认：Docker 镜像构建（[Build]）和推送（[Push]）阶段均完全成功，失败仅发生在 CI 框架层 `[Check]` 阶段的 eulerpublisher 测试脚本中。该问题属于 eulerpublisher 打包缺陷，需由 eulerpublisher 维护者在包的构建流程中对该脚本执行 `dos2unix` 或在 CI 流水线中进行预处理。PR 新增的 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及元数据文件均与此次失败无关。

## 潜在风险
无。不做代码修改，不影响现有功能。