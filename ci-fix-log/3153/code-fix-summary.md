# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），CI 工具 `eulerpublisher` 的 appstore 路径校验逻辑中存在路径格式不匹配：期望 `/README.md` 但 git diff 上报 `README.md`（缺少前导 `/`），与 PR #3153 的文档变更内容无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败类型为 `lint-error`，根因定位于 CI 工具 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布路径校验逻辑。该工具在比较文件路径时未进行路径规范化（添加前导 `/`），导致 `git diff` 上报的 `README.md` 与期望的 `/README.md` 字符串匹配失败。

PR #3153 仅更新了 `README.md` 中基础镜像 tags 的文档内容，属于纯文档类变更，文件路径和内容均正确。此 CI 失败是基础设施工具缺陷，应在 eulerpublisher 仓库中修复路径比较逻辑，而非修改本仓库代码。

## 潜在风险
无（无代码变更）