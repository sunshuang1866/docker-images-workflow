# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：eulerpublisher 测试脚本 `bwa_test.sh` 包含 CRLF 行尾导致 `bad interpreter`，与 PR 代码无关，无需修改本仓库代码。

## 修改的文件
无。CI 失败属于 eulerpublisher 基础设施问题，不在本 PR 的仓库范围内。

## 修复逻辑
CI 分析报告明确指出：
- 所有构建步骤（`make` 编译、Docker 镜像构建、Registry 推送）均成功完成。
- 失败仅发生在 eulerpublisher CI 框架的 `[Check]` 阶段，原因是 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的 shebang 行末尾包含 Windows 风格回车符（`\r`/`^M`），导致系统尝试将 `#!/bin/sh\r` 作为解释器路径查找而失败。
- 该文件属于 eulerpublisher 安装包，不在本 PR 的仓库范围内，PR 作者无法修复。

处理方式：由 eulerpublisher CI 工具链维护者将 `tests/container/app/bwa_test.sh` 的行尾从 CRLF 转换为 LF，修复后重跑流水线即可。

## 潜在风险
无。本 PR 的代码变更（新增 openEuler 24.03-LTS-SP4 的 bwa Dockerfile 及文档）本身正确无误。