# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），与本次 PR 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败发生在 CI 工具 `eulerpublisher` 的 [Check] 阶段，根本原因是 `eulerpublisher` 包自带的 `bwa_test.sh` 测试脚本使用了 Windows 换行符（CRLF），导致 shell 将 shebang 行解释为 `/bin/sh\r` 而报 "bad interpreter: No such file or directory"。

PR #2995 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及修改元数据文件（README.md、image-info.yml、meta.yml），Docker 构建与推送阶段全部成功完成，镜像本身没有问题。

此问题需由 CI 工具维护者修复：将 `eulerpublisher` 仓库中的 `bwa_test.sh` 文件的换行符从 CRLF 转换为 LF（Unix 格式），重新打包/发布后 CI 流水线即可恢复正常。

## 潜在风险
无。本次 PR 的代码无需任何修改，保持原样即可。