# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非 PR 代码变更导致。

## 修改的文件
无。PR 涉及的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）均无需改动。

## 修复逻辑
CI 分析报告确认：Docker 镜像构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`）。失败发生在 `[Check]` 后置测试阶段，根因是 `eulerpublisher` Python 包内置的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 包含 Windows 风格换行符（CRLF），导致 shebang `#!/bin/sh` 末尾携带 `\r` 字符，系统将其解释为查找 `/bin/sh\r` 解释器，从而报 `bad interpreter: No such file or directory`。

该问题与 PR #2995 的所有代码变更无关，应由 CI 平台维护方修复 `eulerpublisher` 包中测试脚本的换行符后重新发布。

## 潜在风险
无