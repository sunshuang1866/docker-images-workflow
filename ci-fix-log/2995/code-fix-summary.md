# 修复摘要

## 修复的问题
无需代码修改。本次 CI 失败为 `infra-error`，由 CI 工具 `eulerpublisher` 内置的 `bwa_test.sh` 测试脚本包含 CRLF 行尾导致，与本次 PR 提交的代码无关。

## 修改的文件
无。PR 涉及的文件（Dockerfile、README.md、meta.yml、image-info.yml）均无需修改。

## 修复逻辑
CI 分析报告明确指出：Docker 镜像构建和推送均已完成并成功（`[Build] finished`、`[Push] finished` 均正常），失败仅发生在 `[Check]` 阶段。该阶段调用 `eulerpublisher` 包中预置的 `tests/container/app/bwa_test.sh` 测试脚本时，因脚本文件的 shebang 行包含回车符（`#!/bin/sh\r`），Linux 无法找到 `/bin/sh\r` 解释器，报 `bad interpreter: No such file or directory`。此问题需要在 `eulerpublisher` 上游仓库中修复该测试脚本的行尾格式（CRLF → LF），或在 `.gitattributes` 中配置防止 CRLF 转换，而非在本仓库中修改任何代码。

## 潜在风险
无。本次 PR 的代码变更与 CI 失败无关，无需对本仓库做任何改动。