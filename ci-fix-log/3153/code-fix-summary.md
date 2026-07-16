# 修复摘要

## 修复的问题
无需代码修改 — 此次 CI 失败为基础设施错误（infra-error），与 PR #3153 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败类型为 `infra-error`，置信度**高**。CI 流水线中的 appstore 发布规范预检脚本 `eulerpublisher/update/container/app/update.py` 对仓库根目录的 `README.md` 执行了路径校验，要求其路径格式为 `/README.md`（以 `/` 开头）。但 `README.md` 是仓库级文档，并非应用镜像文件，此路径校验属于 CI 工具误报。

PR #3153 仅为文档变更（更新可用镜像 Tags 列表），未新增任何镜像目录、Dockerfile 或元数据文件，与 CI 预检逻辑的路径校验规则毫无关联。修复此 CI 失败需要由 CI/平台维护者更新 `update.py` 中的路径校验逻辑，将仓库根目录文档文件排除在检查范围之外。

## 潜在风险
无