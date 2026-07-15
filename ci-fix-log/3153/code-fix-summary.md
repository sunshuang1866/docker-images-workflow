# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为基础设施错误（infra-error），由 CI 工具 `eulerpublisher` 的 appstore 规范检查逻辑触发，与 PR 的文档变更内容无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告将该失败归类为 `infra-error`，根因在于 CI 工具 `eulerpublisher/update/container/app/update.py` 中 appstore 规范检查的路径校验逻辑：`git diff` 输出的相对路径（如 `README.md`）与工具内部期望的绝对路径格式（如 `/README.md`）不匹配，导致校验项误报 FAILURE。

PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的文档内容（基础镜像 Tags 列表更新），变更本身正确无误。该失败需要由 `eulerpublisher` 工具维护者修复路径校验逻辑（添加路径格式归一化，或在变更文件列表中排除根级非镜像文件），而非修改本 PR 的代码。

由于 `pr.changed_files` 限定为 `['README.md']`，且分析报告明确指出是基础设施问题，按照修复原则不予修改代码。

## 潜在风险
无