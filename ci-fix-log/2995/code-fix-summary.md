# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施错误（infra-error），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败发生在 `[Check]` 阶段的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`，该脚本来自 eulerpublisher 包，不属于本仓库。
- Docker 构建（`[Build]`）和推送（`[Push]`）阶段均已成功完成，PR 所修改的 Dockerfile 无任何问题。
- 根本原因是 eulerpublisher 包中的 `bwa_test.sh` 包含 Windows 风格的 CRLF 行尾符（`\r\n`），导致 shell shebang 被错误解析为 `/bin/sh^M`，脚本无法执行。

此修复应在 eulerpublisher 仓库侧完成（将 `bwa_test.sh` 的行尾格式从 CRLF 转为 LF），不属于当前 PR 的修改范围。

## 潜在风险
无 — 本仓库无需任何代码变更。