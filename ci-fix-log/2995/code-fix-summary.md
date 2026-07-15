# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。`eulerpublisher` 包中的测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF），导致 shebang 解析异常（`/bin/sh^M: bad interpreter`）。

## 修改的文件
无。此失败与 PR 变更无关，PR 中修改的所有文件（Dockerfile、README.md、image-info.yml、meta.yml）均为正确的新增内容，Docker 镜像构建和推送均已成功完成。

## 修复逻辑
分析报告确认此为 `infra-error`，失败发生在 CI 流水线的 `[Check]` 阶段，原因是 CI 节点上安装的 `eulerpublisher` 包自带的测试脚本 `bwa_test.sh` 存在 CRLF 行尾问题。该脚本不属于本次 PR 变更范围，无需修改任何 PR 代码。修复应在上游 `eulerpublisher` 仓库中将该脚本的行尾从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`），然后更新 CI 构建节点上的 `eulerpublisher` 包版本。

## 潜在风险
无。本 PR 无需代码修改，不引入任何风险。