# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：`eulerpublisher` appstore 预检工具对纯文档变更 PR（仅修改 `README.md`）触发了路径校验，因路径格式不一致（缺少前导 `/`）报 Path Error。源代码无 bug，无需修改。

## 修改的文件
无。本 PR 为纯文档变更，代码无需修改。

## 修复逻辑
CI 分析报告判定为 `infra-error`，根因在 CI 工具 `eulerpublisher/update/container/app/update.py` 未排除根级文档文件的检查，且路径比对时未做归一化处理。此问题需在 CI 工具侧修复，不在本 PR 代码范围内。

## 潜在风险
无