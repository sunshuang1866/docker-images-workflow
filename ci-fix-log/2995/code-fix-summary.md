# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error）。

## 修改的文件
无。PR 中所有文件（Dockerfile、README.md、image-info.yml、meta.yml）均无需变更。

## 修复逻辑
CI 失败发生在 [Check] 测试阶段，根因是 eulerpublisher Python 包中内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾附带不可见的回车符 `\r`，内核无法找到解释器 `/bin/sh\r`。

此问题与 PR #2995 的代码变更完全无关：
- Docker 镜像的构建和推送阶段全部成功（`[Build] finished`，`[Push] finished`）
- PR 仅新增了 bwa 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及元数据文件
- 失败发生在 CI 流水线调用外部工具 eulerpublisher 的预置测试脚本时

**需要 CI 运维团队处理**：将 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`），然后重新打包发布。

## 潜在风险
无 — 未修改任何代码，不存在引入新问题的风险。