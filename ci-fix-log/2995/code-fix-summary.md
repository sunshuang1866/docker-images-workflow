# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**，由 eulerpublisher CI 工具内置的 `bwa_test.sh` 测试脚本携带 Windows 换行符（CRLF）导致，与 PR #2995 的代码变更无关。

## 修改的文件
无

## 修复逻辑
分析报告明确指出失败发生在 CI 基础设施的 `[Check]` 测试阶段，而非构建或代码层面：
- Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）均已成功完成
- 失败原因是 eulerpublisher 工具包中 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 文件的 shebang 行末尾携带 `\r`（CRLF），导致系统将 `/bin/sh\r` 视为解释器路径
- 这是 eulerpublisher CI 工具的缺陷，需要由 eulerpublisher 维护者将该测试脚本的换行符从 CRLF 转换为 LF，或在 CI 执行前对脚本做 `dos2unix` 处理
- PR 变更的文件（Dockerfile、README.md、doc/image-info.yml、meta.yml）均不涉及换行符问题，且 Dockerfile 构建已成功验证

## 潜在风险
无。此修复不涉及任何代码修改，原始 PR 的变更文件质量良好，无需调整。