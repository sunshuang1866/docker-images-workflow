# 修复摘要

## 修复的问题
无代码修改。本次失败为 CI 基础设施问题（infra-error），eulerpublisher 工具包内置的 `bwa_test.sh` 测试脚本含有 Windows CRLF 行尾，导致 shebang 解析失败（`/bin/sh^M: bad interpreter`），与 PR #2995 的代码变更无关。

## 修改的文件
无。PR 涉及的文件（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 等）均无问题，Docker 镜像构建与推送均已成功。

## 修复逻辑
分析报告确认：
- Docker 镜像构建成功（`#7 DONE 199.0s`）
- 镜像推送成功（`#8 DONE 8.4s`、`[Push] finished`）
- 失败仅发生在 CI [Check] 阶段，根因是 `eulerpublisher` 包中 `bwa_test.sh` 使用 CRLF 行尾

此问题需要在 CI 基础设施侧修复：将 `eulerpublisher/tests/container/app/bwa_test.sh` 的行结束符从 CRLF 转换为 LF（如使用 `dos2unix`），然后重新打包/部署。源码仓库无需任何代码修改。

## 潜在风险
无