# 修复摘要

## 修复的问题
无需代码修改。CI 失败被诊断为 **infra-error**：appstore 发布预检工具 (`eulerpublisher/update/container/app/update.py`) 错误地对纯文档 PR 中变更的根级 README 文件执行了路径校验，导致误报 FAILURE。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因在于 CI appstore 预检工具的 diff 分析逻辑未过滤根级纯文档文件（`README.md`、`README.en.md`），将其错误纳入 appstore 路径校验范围。该问题与 PR 变更内容无关（PR 仅增补了可用镜像 Tags 列表），修复点位于 `eulerpublisher/update/container/app/update.py`（不在 `pr.changed_files` 允许修改的文件列表中）。根据任务指令，infra-error 情况下不强行修改代码。

## 潜在风险
无 — 未对任何源代码做修改。实际修复需由 CI 基础设施维护者在 `update.py` 中增加过滤逻辑，将根级 README 文件排除在 appstore 路径校验之外。