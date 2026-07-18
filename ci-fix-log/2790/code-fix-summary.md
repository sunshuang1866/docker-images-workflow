# 修复摘要

## 修复的问题
CI 基础设施误报 — appstore 预检工具对纯文档更新 PR（仅修改 `README.md`）错误地报告路径校验失败。`README.md` 实际已在仓库根目录 `/README.md`，无需代码修改。

## 修改的文件
无 — 此失败属于 infra-error，`README.md` 已位于正确路径，不需要修改任何源文件。

## 修复逻辑
CI 分析报告（infra-error，置信度：中）指出：当 PR diff 仅包含根级 `README.md` 变更（无伴随的 app Dockerfile / meta.yml 提交）时，CI 的 appstore 预检工具 `update.py` 中的路径匹配逻辑产生误报。该问题根源在 CI 工具侧（`_check_path` 校验逻辑），不在本仓库源码中。按照项目规范，infra-error 场景下不应强行修改代码。

## 潜在风险
无