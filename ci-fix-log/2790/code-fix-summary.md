# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 失败根因位于 `eulerpublisher/update/container/app/update.py`（CI appstore 发布规范预检工具），不属于本 PR 的变更文件（`README.md`），也不在 `pr.changed_files` 允许修改的范围内。

具体问题：
1. **路径归一化缺失**：CI 工具从 `git diff` 获取的变更路径为 `README.md`（无前导 `/`），而内部校验规则期望路径为 `/README.md`（带前导 `/`），字符串比对不匹配导致误报 `[Path Error]`。
2. **触发条件过宽**：纯文档变更 PR（仅修改 `README.md`）不应触发 appstore 发布规范检查，但当前 CI 流水线未做区分。

PR #2790 仅更新了 `README.md` 中的 Supported Tags 链接，代码变更本身完全正确，不存在需要修复的问题。该 CI 失败需由 CI 工具链维护者在 `eulerpublisher` 仓库中修复路径比对逻辑或优化触发条件。

## 潜在风险
无 — 未对任何文件做修改。