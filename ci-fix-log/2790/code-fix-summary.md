# 修复摘要

## 修复的问题
CI appstore 路径校验器将根级文档文件（`README.md`、`README.en.md`）误判为应用镜像文件，报 `[Path Error]`。此失败由 CI 基础设施校验脚本 `eulerpublisher/update/container/app/update.py` 的逻辑缺陷引起，与 PR 变更内容无关。

## 修改的文件
无需修改任何代码文件。

## 修复逻辑
根据 CI 分析报告，失败根因在于 `update.py:273` 的 appstore 规范校验器将所有 PR 变更文件纳入路径检查，但根级纯文档文件（`README.md`、`README.en.md`）不属于任何应用镜像条目，不应要求符合应用镜像路径规范。

由于：
1. 当前 PR 仅修改了 `README.md` 和 `README.en.md` 两个根级文档文件，内容本身完全正确
2. 校验器代码 `update.py` 不在允许修改的文件列表（`pr.changed_files`）中
3. 此问题本质上属于 **infra-error**（CI 基础设施问题），而非代码问题

因此不需要对 `README.md` / `README.en.md` 做任何修改。正确的修复应落在 `eulerpublisher/update/container/app/update.py` 中，为根级文档文件（路径不包含任何场景子目录如 `AI/`、`Bigdata/` 等的文件）增加豁免逻辑。

## 潜在风险
无。PR 涉及的两个文件内容正确，无需改动。