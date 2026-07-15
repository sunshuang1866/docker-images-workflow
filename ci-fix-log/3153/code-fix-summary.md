# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范检查工具（`update.py`）对纯文档修改的 PR 错误执行了路径校验，将仓库根目录下的 `README.md` 误判为不符合 appstore 镜像路径规范。此问题与 PR 代码变更无关。

## 修改的文件
无。该问题为 CI 基础设施问题（infra-error），不需要修改任何源代码文件，包括 `README.md`。

## 修复逻辑
根据 CI 失败分析报告，失败类型确认为 `infra-error`：
- PR #3153 仅修改了 `README.md`（及 `README.en.md`）中的基础镜像可用标签描述，属于纯文档更新。
- CI 的 `update.py` 工具对所有 PR 一律执行 appstore 发布规范检查，未将仓库根级文档文件（`README.md` 等）纳入白名单排除，导致误报。
- 根因在 CI 流水线配置 / `update.py` 检查逻辑，不在 PR 代码中。

按照任务指令要求，对于 `infra-error` 类型问题，不强行修改代码。需由 CI 管理员调整流水线配置：将根级文档文件加入 appstore 路径校验白名单，或使 appstore 规范检查仅在 PR 涉及应用镜像目录时才触发。

## 潜在风险
无（未修改任何代码）。