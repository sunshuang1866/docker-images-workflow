# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），与 PR #2995 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定为 `infra-error`，置信度高。Docker 镜像构建和推送均已完成（[Build] finished、[Push] finished），所有 7 个构建步骤全部通过。失败仅发生在 CI 后处理阶段的 [Check] 步骤，根因是 eulerpublisher Python 包自带的 `bwa_test.sh` 脚本文件含有 CRLF 行尾（`^M`），导致 `#!/bin/sh\r` 的 shebang 被误认为解释器路径 `/bin/sh\r`（不存在），触发 "bad interpreter: No such file or directory" 错误。

该文件属于 CI 基础设施组件（eulerpublisher 包），不在 PR 变更的文件列表中，也不在当前源码仓库内。因此无需修改本仓库的任何代码。

## 潜在风险
无 — 本仓库代码无需任何修改。建议 CI 基础设施维护者将 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 的行尾格式从 CRLF 转换为 LF 后重新发布。