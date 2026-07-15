# 修复摘要

## 修复的问题
此 CI 失败为 `infra-error`，根因在于 CI 基础设施（`eulerpublisher` 包）的 `bwa_test.sh` 脚本使用了 CRLF 行尾格式，导致 shebang 解释器路径被污染。Docker 镜像的构建和推送阶段均成功完成，失败仅发生在 CI 的 [Check] 测试阶段。**此问题与 PR 代码无关，无需对 PR 代码做任何修改。**

## 修改的文件
无（infra-error，PR 代码无需修改）

## 修复逻辑
CI 分析报告确认：
- 直接失败位置：`/etc/eulerpublisher/tests/container/app/bwa_test.sh`，该文件属于 CI 编排工具 `eulerpublisher` Python 包，不在本仓库的 PR 变更范围内。
- 失败原因：脚本使用 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 中的 `\r` 被内核视为解释器路径的一部分，无法找到 `/bin/sh\r`。
- PR 中所有文件（Dockerfile、README.md、image-info.yml、meta.yml）的变更均正确，镜像构建和推送均已成功。

此问题需由 CI 基础设施团队在 `eulerpublisher` 仓库中修复 `bwa_test.sh` 的行尾格式（CRLF → LF），与当前 PR 代码无关。

## 潜在风险
无（未修改任何代码）