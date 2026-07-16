# 修复摘要

## 修复的问题
无需代码修改 — CI 失败属于基础设施错误（infra-error），而非 PR 变更内容的问题。

## 修改的文件
无

## 修复逻辑
CI appstore 规范校验脚本 `eulerpublisher/update/container/app/update.py:273` 在检测 PR 变更文件时，错误地将仓库根目录的 `README.md` 纳入应用镜像目录路径校验范围，导致 `[Path Error]` 误报。

PR #3153 仅修改了根目录的 `README.md`（更新基础镜像可用 Tag 列表），不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建相关文件，是一个纯文档更新。`README.md` 的内容和格式均正确，无需修改。

该问题的根因在于 CI 校验脚本缺少对仓库根目录文档文件（`README.md`、`README.en.md`）与应用镜像目录文件（`Bigdata/`、`AI/` 等子目录）的区分逻辑。修复应发生在 `update.py` 中，但该文件不在本 PR 的变更文件列表 `['README.md']` 中，超出本次修复范围。

## 潜在风险
无 — PR 变更内容本身正确无误，CI 误报不影响 README.md 文档的正确性。