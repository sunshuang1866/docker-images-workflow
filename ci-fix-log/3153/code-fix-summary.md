# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error），无需 PR 代码修改。

## 修改的文件
无。CI 失败由 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）的路径校验逻辑触发，与 PR 中 `README.md` 的文档内容变更无关。

## 修复逻辑
CI 的 appstore 校验工具将仓库根目录 `README.md` 的变更误判为 appstore 镜像条目，要求其遵循 `{category}/{image}/{version}/{os-version}/README.md` 的路径格式规范，导致 `[Path Error]` 校验失败。根目录 `README.md` 是仓库级文档，不应受此规范约束。

此问题需由 CI 维护方在 `eulerpublisher` 工具侧修复：将仓库根目录文档文件（`README.md`、`README.en.md` 等）加入路径校验豁免列表。PR 作者侧无需且无法通过修改 `README.md` 解决问题。

## 潜在风险
无。本次未修改任何源代码。