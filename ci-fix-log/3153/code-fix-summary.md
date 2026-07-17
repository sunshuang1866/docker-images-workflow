# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），根因在 `eulerpublisher` CI 工具内部的路径规范化缺陷。

## 修改的文件
- 无（infra-error，无需修改 `README.md` 或任何源码文件）

## 修复逻辑
CI 分析报告明确指出：失败类型为 `infra-error`，置信度 **高**。CI 工具 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 路径校验逻辑对 git diff 产生的相对路径 `README.md` 与预期绝对路径 `/README.md` 做字符串严格比对，因缺少前导 `/` 报错。PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的文档标签列表（纯文档更新），代码本身无误。修复应在上游 CI 工具 `eulerpublisher` 中进行，为本仓库开源代码之外的基础设施问题。

## 潜在风险
无。本仓库无需任何代码变更。