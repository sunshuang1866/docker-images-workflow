# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：appstore 发布规范预检脚本 `update.py` 错误地将根级文档文件（`README.md`、`README.en.md`）纳入发布规范校验范围，导致纯文档类 PR 被误拦截。PR #2790 的代码变更本身无错误，无需修改。

## 修改的文件
无代码修改。PR 中变更的文件（`README.md`、`README.en.md`）仅为文档内容更新，无需任何改动。

## 修复逻辑
分析报告判定为 infra-error，失败根因在 CI 流水线侧的 `eulerpublisher/update/container/app/update.py` 脚本，该脚本在校验差异文件时未区分"应用镜像发布变更"与"仓库文档变更"，对根级 `*.md` 文件也执行了 appstore 路径规范校验。修复应在 CI 侧脚本中增加根级文档文件的过滤逻辑，不涉及本 PR 的代码变更。

## 潜在风险
无。PR 本身改动纯属文档维护，不存在代码层面的风险。