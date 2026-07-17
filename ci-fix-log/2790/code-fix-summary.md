# 修复摘要

## 修复的问题
CI 基础设施问题：外部 CI 工具 `eulerpublisher` 将根级文档文件 `README.md` 错误纳入 appstore 发布规范检查，导致路径校验失败。PR 本身仅为文档更新（Tags 列表修正），无代码错误。

## 修改的文件
无需修改任何源代码文件。

## 修复逻辑
分析报告确认这是 CI 基础设施问题（`infra-error`）。根因是 CI 流水线中的 `eulerpublisher/update/container/app/update.py` 工具对 PR 变更文件进行 appstore 发布规范预检时，未区分根级文档文件与应用镜像目录文件，将 `README.md` 纳入检查范围。根级 `README.md` 不遵循应用镜像的路径规范（`{category}/{image}/{version}/{os-version}/`），因此路径校验失败。

PR #2790 仅修改了 `README.md`（更新可用镜像 Tags 列表），属于纯文档修正，PR 内容本身无错误。此问题需由 CI 管理员在 `eulerpublisher` 工具中增加文件路径过滤逻辑（排除根级 `README.md`、`README.en.md` 等文档文件），或在此类文档 PR 上跳过 appstore 发布规范检查 job。源代码仓库无需修改。

## 潜在风险
无。未修改任何代码，不会引入新问题。