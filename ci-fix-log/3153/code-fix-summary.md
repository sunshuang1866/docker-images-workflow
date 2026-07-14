# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**——appstore 发布规范检查器错误地对仓库根级文档文件（`README.md`、`README.en.md`）进行了路径校验，而这些文件不属于任一镜像发布目录，不应被纳入校验范围。PR #3153 的文档变更本身正确无误。

## 修改的文件
无。本次为 CI 基础设施误报，无需对任何源代码文件进行修改。

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`（置信度：高）。PR 仅修改了 `README.md` 和 `README.en.md` 中"可用镜像 Tags"表格的内容，属于纯文档变更。CI 流水线中 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑将根级文件也纳入了 appstore 发布规范检查，导致误报。此问题需要在 CI 流水线层面（`update.py`）增加根级文件的过滤或跳过逻辑，而非修改 PR 中的文档文件。

由于该修复文件（`eulerpublisher/update/container/app/update.py`）不在本次 PR 的 `pr.changed_files` 允许修改列表中，且分析报告明确标注为 `infra-error`，按照修复规范，不强制修改代码。

## 潜在风险
无。不涉及任何代码变更。