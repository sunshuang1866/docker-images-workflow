# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 `infra-error`：CI 流水线的 appstore 发布规范校验工具 (`eulerpublisher/update/container/app/update.py`) 错误地将仓库根目录文档文件 `README.md` 纳入应用镜像路径格式校验范围，产生误报。

## 修改的文件
无。PR #3153 仅修改 `README.md`（文档内容更新），该变更本身正确无误。

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`（CI 基础设施问题），根因在于 CI 校验逻辑未将根目录文档文件（`README.md`、`README.en.md`）排除在 appstore 路径格式校验之外。该问题修复需在 CI 基础设施代码（`eulerpublisher`）中增加路径过滤逻辑，而非在源码仓库中修改代码。PR 变更的 `README.md` 内容本身没有问题，无需任何代码修改。

## 潜在风险
无。`README.md` 变更不受此 CI 误报影响，可正常合入。