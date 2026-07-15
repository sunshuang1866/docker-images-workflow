# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。

## 修改的文件
无

## 修复逻辑

CI 失败分析报告确认：此次 CI 失败与 PR #2995 的代码变更**完全无关**。

- PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新了三个元数据文件（`README.md`、`image-info.yml`、`meta.yml`），均不涉及 `bwa_test.sh` 测试脚本。
- Docker 镜像的构建和推送阶段均成功完成（日志中可见 `[Build] finished`、`[Push] finished`）。
- 失败发生在 CI 后处理 [Check] 阶段，根因是 `eulerpublisher` 包中自带的 `bwa_test.sh` 脚本使用 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带回车符 `\r`，内核将解释器路径解析为不存在的 `/bin/sh\r`，脚本无法执行。

此问题需由 CI 管理员修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件，将其换行符从 CRLF 转换为 LF（例如在 CI runner 上执行 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件，或从源头确保包发布时包含 Unix 换行符的脚本文件）。

## 潜在风险
无