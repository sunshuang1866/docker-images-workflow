# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），与 PR #2995 的变更无关。

## 修改的文件
无。PR 变更的文件均不涉及 CI 失败根因。

## 修复逻辑
CI 失败发生在 `[Check]` 阶段运行 `bwa_test.sh` 测试脚本时，根因是 CI 基础设施组件 `eulerpublisher` 软件包中的 `bwa_test.sh` 文件包含 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 无法被内核识别为有效解释器，脚本执行失败。

Docker 镜像的构建（`[Build]` 阶段）和推送（`[Push]` 阶段）均已成功完成，PR 变更的 4 个文件（`Dockerfile`、`README.md`、`image-info.yml`、`meta.yml`）均不涉及 shell 脚本，也不涉及 `eulerpublisher` 测试框架。此问题需要 CI 基础设施维护者在 `eulerpublisher` 软件包中修复，将该测试脚本的换行符从 CRLF 转换为 LF（如使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理）。

## 潜在风险
无。PR 代码本身没有问题，修复应由 CI 基础设施侧完成。