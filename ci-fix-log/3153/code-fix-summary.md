# 修复摘要

## 修复的问题
CI appstore 发布规范预检脚本（`eulerpublisher/update/container/app/update.py`）错误地将仓库根级 README 文件（`README.md`、`README.en.md`）纳入了 image 子目录的路径校验，导致 PR #3153（仅修改根级文档内容）被误报为 lint-error。这是 CI 基础设施的 bug，非 PR 代码变更引入的问题。

## 修改的文件
无。本次 CI 失败的根因在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中，该文件不在 PR #3153 的变更文件列表（`['README.en.md', 'README.md']`）内，且两个 README 文件均为纯文档文件，无法通过修改 README 内容来绕过 CI 校验。

## 修复逻辑
该问题属于 CI 基础设施错误（infra-error），需要由 CI 维护者修改 `update.py` 中的路径校验逻辑，增加对仓库根级非 image 文件的豁免规则。具体来说，应在 `_validate_path` 中对不在任何 `image-list.yml` 覆盖的 category 目录下的文件跳过 appstore 路径规范检查。此类文件包括：根级 `README.md`、`README.en.md`、`.gitignore`、`LICENSE` 等。

## 潜在风险
无。本次未对任何源代码文件进行修改。