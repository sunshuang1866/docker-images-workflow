# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无。PR 涉及的 4 个文件（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`）均正确无误，构建和推送均已完成成功。

## 修复逻辑
CI 失败发生在 [Check] 后处理阶段，根因是 `eulerpublisher` 测试框架中的 `bwa_test.sh` 脚本文件的 shebang 行携带了 Windows 风格换行符（CRLF），导致 `#!/bin/sh\r` 被解析时找不到 `/bin/sh\r` 解释器。此文件不在当前仓库中（属于 `eulerpublisher` 包），开发者需要在 `eulerpublisher` 仓库中将 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF（如使用 `dos2unix` 或 `sed -i 's/\r$//'`）。

## 潜在风险
无。未修改任何代码。