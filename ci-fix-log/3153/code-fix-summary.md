# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无。PR #3153 仅包含 `README.md` 和 `README.en.md` 的文档内容更新（基础镜像 Tags 列表），这些文件内容正确，无需修改。

## 修复逻辑
CI 失败分析报告将该失败归类为 `infra-error`。根因是 CI 的 appstore 发布规范预检脚本（`eulerpublisher/update/container/app/update.py`）错误地将仓库根级项目文档文件（`README.md`、`README.en.md`）纳入路径校验范围。该检查本应仅针对 `AI/`、`Bigdata/` 等应用镜像场景目录内的文件，不应审查仓库根级文档。PR #3153 是纯文档变更，不影响任何应用镜像的构建或发布。需要修复的是 CI 基础设施脚本（`eulerpublisher/update/container/app/update.py`），该文件不在本 PR 的变更范围内，也不在允许修改的文件列表中。

## 潜在风险
无代码修改，无风险。建议在 CI 侧修复 `eulerpublisher/update/container/app/update.py` 增加根级文档文件的豁免逻辑，或使用 label 跳过方式允许纯文档 PR 绕过该检查。