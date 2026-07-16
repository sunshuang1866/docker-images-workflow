# 修复摘要

## 修复的问题
CI 基础设施故障（infra-error），无需修改 PR 中的任何代码文件。CI 的 appstore 发布规范预检工具错误地将仓库根目录的 `README.md`（全局项目文档）纳入 image 层级路径规则进行校验，导致校验误报。

## 修改的文件
无（infra-error，非代码层问题）

## 修复逻辑
CI 分析报告确认：PR #3153 对 `README.md` 的文档更新本身正确无误。失败根因是 CI 工具 `eulerpublisher/update/container/app/update.py:273` 的校验逻辑缺陷 — 通过 `git diff` 收集变更文件后，未过滤掉仓库根目录下的非镜像文件（如 `README.md`、`README.en.md` 等），导致对不隶属于任何镜像子目录的根级文件执行了 appstore 路径规范校验。此问题需在 CI 工具侧修复：在收集 `git diff` 变更文件后，应过滤掉仓库根目录下不匹配 `{category}/{image}/{version}/{os-version}/` 结构的非镜像文件，仅对镜像目录内的文件执行路径校验。

## 潜在风险
无（未修改任何代码）