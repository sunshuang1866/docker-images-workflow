# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：`eulerpublisher` 工具内置测试脚本 `bwa_test.sh` 使用 Windows 换行符（CRLF），导致 shebang 行被内核误解析为 `/bin/sh\r`（不存在），引发 `bad interpreter: No such file or directory` 错误。

## 修改的文件
无。此错误与 PR 代码变更无关，无需修改任何源代码。

## 修复逻辑
CI 分析报告确认：
- Docker 镜像构建和推送均已成功完成（`[Build] finished`、`[Push] finished`）。
- 失败仅发生在 CI 的 `[Check]` 阶段，该阶段调用 `eulerpublisher` 工具预装的系统级测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`。
- 该脚本本身存在 CRLF 换行符缺陷，属于 CI 基础设施问题，需要 `eulerpublisher` 维护者将该脚本转换为 Unix 换行符（LF）。
- PR 修改的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均无问题。

## 潜在风险
无。待 CI 基础设施团队修复 `bwa_test.sh` 换行符问题后，重新触发 CI 流水线即可。