# 修复摘要

## 修复的问题
CI appstore 预检脚本误将仓库根目录的 README 文件纳入 appstore 路径校验范围，产生 `[Path Error]` 误报。无需修改 `README.en.md` 或 `README.md`。

## 修改的文件
无 — README 文件本身内容正确，不存在需要修复的问题。

## 修复逻辑
CI 失败根因是 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检逻辑未排除仓库根目录的文档文件（`README.md`、`README.en.md`），这些文件不应受 appstore 路径规则约束。这与历史 PR #2512 中 `.claude/` 目录 README 文件的处理模式一致。

修复应在 `update.py` 中添加对根层级非应用镜像文档文件的豁免逻辑，但该文件不在本次 PR 的 `changed_files` 范围内（仅包含 `README.en.md` 和 `README.md`），依据修复约束不得修改。README 文件本身无任何内容错误，无需改动。

## 潜在风险
无 — 本次未对任何文件做修改，不会引入风险。若需彻底解决此 CI 误报，需由有权修改 `eulerpublisher` 的维护者在 `update.py` 中添加根目录文档文件的路径豁免规则。