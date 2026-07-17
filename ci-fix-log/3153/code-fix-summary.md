# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：appstore 发布规范校验工具 (`eulerpublisher/update/container/app/update.py`) 错误地将仓库根级 `README.md` 纳入应用镜像路径格式校验范围，导致纯文档类 PR 的 CI 门禁失败。PR #3153 对 `README.md` 的变更内容（更新基础镜像可用 tags 列表）本身正确无误，无需修改。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败根因是 appstore 校验工具 `update.py` 的文件过滤逻辑缺陷——该工具设计用于校验应用镜像 PR（需包含 `{category}/{image}/{version}/README.md` 目录结构），但未排除仓库根级文件（`README.md`、`README.en.md`），导致根级 README.md 的路径格式不满足应用镜像路径校验规则而报 `[Path Error]`。PR #3153 仅涉及 `README.md` 的文档内容更新，属于纯文档类变更，不应触发应用镜像路径格式检查。这是一个 CI 工具侧的问题，应在 `update.py` 中增加对根级文件的排除过滤逻辑，不在当前 PR 的文件修改范围内。

## 潜在风险
无——当前 PR 的 `README.md` 内容变更正确，不涉及功能代码。修复应在 CI 基础设施侧完成，与此 PR 无关。