# 修复摘要

## 修复的问题
无代码修复 — 本次 CI 失败为基础设施问题（infra-error），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认，失败发生在 eulerpublisher 测试框架的内置脚本 `bwa_test.sh`，该脚本包含 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 中的 `\r` 使内核无法找到正确的解释器。Docker 镜像的构建和推送均已成功完成。

此失败与 PR #2995 新增的 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及相关元数据文件完全无关，属于 CI 工具链 eulerpublisher 包的自身缺陷。PR 代码无需任何修改。

修复应由 CI 基础设施团队在 eulerpublisher 源码仓库中将 `tests/container/app/bwa_test.sh` 的换行符从 CRLF 转换为 LF 后重新发布包来解决。

## 潜在风险
无