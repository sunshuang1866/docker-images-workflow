# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error，根因是 CI 工具 `update.py` 的 appstore 路径校验逻辑存在缺陷（git diff 产出的相对路径 `README.md` 与校验期望的绝对路径 `/README.md` 不匹配），而非 PR 代码问题。

## 修改的文件
无

## 修复逻辑
该 PR (#3153) 仅修改了 `README.md`，更新基础镜像可用 tag 列表，属于纯文档变更。CI 失败完全是 CI 基础设施工具 `eulerpublisher/update/container/app/update.py` 中的 bug 所致——该工具对根级文档文件的路径规范化逻辑有缺陷，导致误报。此问题需在 CI 工具层面修复，而非在 PR 代码层面。当前 PR 的文档内容变更正确无误，无需任何代码修改。

## 潜在风险
无