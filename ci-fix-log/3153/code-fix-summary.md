# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 appstore 发布规范校验脚本（`eulerpublisher/update/container/app/update.py:273`）的路径前缀匹配逻辑问题导致，而非 PR 中 README.md 的内容问题。

## 修改的文件
- 无（未修改任何文件）

## 修复逻辑
CI 的 appstore 校验工具在判断文件路径时存在前缀不匹配：脚本期望路径格式为 `/README.md`（带前导 `/`），而 git diff 实际输出的路径为 `README.md`（不带前导 `/`），导致纯文档类 PR 被误判为 `Path Error`。该问题源于 CI 校验工具本身对纯文档变更（仅包含根级 `.md` 文件）的兼容性不足，与 README.md 的实际内容无关。PR 中的 README.md 内容正确无误，无需修改。

## 潜在风险
无。此修复不涉及任何代码变更。