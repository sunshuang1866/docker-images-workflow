# 修复摘要

## 修复的问题
CI appstore 预检工具误将根目录下的纯文档文件（README.md / README.en.md）作为镜像上架项进行路径校验，导致文档类 PR 被误报失败。**该失败属于 CI 基础设施问题（infra-error），非 PR 代码变更的错误，无需对 README 文件做代码修改。**

## 修改的文件
无。PR 变更的 README 文件内容正确，不存在需要修复的 bug。

## 修复逻辑
- PR #3153 仅更新了 README 中基础镜像可用 tags 列表，属于纯文档变更。
- CI 失败的根因在于 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检逻辑，它对所有变更文件强制进行路径格式校验，未排除根目录下的 README 等文档文件。
- 该工具不在 PR `changed_files` 范围内，且属于 CI 基础设施层问题，应由 CI 工具维护者通过以下方式修复：
  - 在 `update.py` 的差异检测逻辑中增加对根目录 README 文件的白名单过滤；或
  - 在 CI 工作流中增加前置判断：当所有变更文件均不属于镜像目录结构时跳过 appstore 预检。

## 潜在风险
无。本次未修改任何源代码。