# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：CI 工具 `eulerpublisher` 的 appstore 路径校验逻辑将仓库根级 `README.md` 误判为应用镜像 README，导致路径校验失败。PR #3153 仅修改了根级 `README.md` 中的基础镜像 tags 列表，属于纯文档维护，与 CI 检查的设计缺陷无关。

## 修改的文件
无。`pr.changed_files` 中的 `README.md` 内容本身正确无误，无需修改。

## 修复逻辑
分析报告明确指出：
- 失败类型为 `infra-error`（CI 基础设施问题）
- "PR 的改动**未触发**该失败"
- "该失败与 PR 代码变更内容无关"

根因是 CI 工具 `eulerpublisher`（`update/container/app/update.py:273`）在执行 appstore 发布规范检查时，未排除仓库根级文档文件（`/README.md`、`/README.en.md` 等），将根级 README 纳入了 appstore 镜像目录结构的路径校验范围。由于根级 README 的路径深度不符合 appstore 镜像的 `{category}/{image-name}/{version}/.../README.md` 层级要求，校验被判定为 FAILURE。

此问题需要由 CI 基础设施团队修复 `eulerpublisher` 工具的路径过滤逻辑，而非修改 PR 中的源码文件。

## 潜在风险
无。未对任何文件进行修改。