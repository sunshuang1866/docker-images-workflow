# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 eulerpublisher 工具链中的 `bwa_test.sh` 测试脚本包含 CRLF 行尾导致，属于 CI 基础设施问题（infra-error），与本次 PR 的代码变更无关。

## 修改的文件
无。PR 涉及的 4 个文件（Dockerfile、README.md、image-info.yml、meta.yml）的 Docker 镜像构建与推送均已成功，无需任何修改。

## 修复逻辑
CI 分析报告确认：失败类型为 `infra-error`，根因是 eulerpublisher 软件包中 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 的 shebang 行带有 Windows 回车符（`\r`），导致 Linux 内核将解释器路径解析为 `/bin/sh\r`，报 `bad interpreter`。PR 的 Docker 镜像构建（#7 DONE）和推送（[Push] finished）均成功完成，失败发生在镜像构建之后的 CI Check 阶段（eulerpublisher 测试框架），与 PR 代码完全无关。

修复应在 eulerpublisher 上游仓库中进行：将该测试脚本的换行符从 CRLF 转换为 LF（如使用 `dos2unix` 或 `sed -i 's/\r$//'`），并检查 `.gitattributes` 配置强制 `*.sh` 文件使用 LF。

## 潜在风险
无。本次未修改任何代码文件。