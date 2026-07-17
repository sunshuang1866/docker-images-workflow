# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检工具对根级 `README.md` 的路径格式校验逻辑触发 — 工具预期路径为 `/README.md`（绝对路径格式），但 git diff 产生的是 `README.md`（相对路径），导致 `[Path Error]`。PR 的 `README.md` 本身内容无错误。

## 修改的文件
- 无代码修改。

## 修复逻辑
PR #2790 仅修改了根级 `README.md`（纯文档更新，新增 `24.03-lts-sp3`、`25.09` 等镜像 tag 信息）。CI 失败根因是 CI 基础设施工具（`eulerpublisher` appstore 发布规范预检脚本）的路径格式校验逻辑不兼容 git diff 的相对路径，且根级 README 本不应触发 appstore 发布流程的路径校验。此问题需要在 CI 工具或 CI 触发规则层面修复（例如排除仅修改根级文档的 PR，或调整 `update.py` 中的路径匹配逻辑），不在当前 PR 可修改文件范围内。

## 潜在风险
无。未做任何代码修改。