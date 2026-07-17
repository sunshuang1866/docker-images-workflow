# 修复摘要

## 修复的问题
无代码修改。CI 失败为 **infra-error**，根因是 eulerpublisher 测试框架中的 `bwa_test.sh` 脚本使用了 Windows CRLF 行尾符，导致 shebang 被解析为 `#!/bin/sh^M`，shell 无法执行。此问题不在当前 PR 仓库范围内。

## 修改的文件
无。所有 PR 变更文件（Dockerfile、README.md、image-info.yml、meta.yml）均正确无误，Dockerfile 构建与推送阶段已成功完成。

## 修复逻辑
分析报告确认：PR 提交的 Dockerfile 已成功构建并推送（日志中 `[Build] finished` 和 `[Push] finished`），失败仅发生在 CI 的 `[Check]` 阶段。该阶段调用 eulerpublisher 工具链中的 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`，该脚本因 CRLF 行尾问题无法被 bash 执行。修复需在 eulerpublisher 仓库中将该脚本的行尾从 CRLF 转换为 LF（使用 `dos2unix` 或编辑器行尾转换功能），与当前 PR 的代码无关。

## 潜在风险
无——当前 PR 无需修改任何代码。