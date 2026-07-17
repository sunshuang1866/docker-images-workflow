# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为 infra-error，系 `eulerpublisher` 工具的 appstore 路径校验缺陷导致，与 PR 实际变更内容无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：PR #3153 是一个纯文档变更，仅更新了 `README.md` 中可用基础镜像 tag 列表。CI 失败是因为 `eulerpublisher` 工具对所有变更文件无差别执行 appstore 路径规范检查，将不属 appstore 范畴的根级 `README.md`（路径 `/README.md`）误标记为 `[Path Error]`。该文件本身路径正确、内容无问题，属于 CI 工具缺陷，无需对 `README.md` 做任何代码修改。

## 潜在风险
无 — 未修改任何源码文件。