# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），由 CI 端 `eulerpublisher` 工具的 appstore 路径校验逻辑误将根目录纯文档文件 `README.md` 纳入镜像发布规范校验范围导致。

## 修改的文件
无。PR #3153 仅修改根目录 `README.md`（更新基础镜像可用 tags 列表），文件内容正确，不存在任何需要修复的代码或文档问题。

## 修复逻辑
CI 分析报告确认：此 PR 为纯文档更新，无 Dockerfile 或构建逻辑变更。CI 工具 `eulerpublisher/update/container/app/update.py:273` 在校验变更文件时未能区分"仓库根目录文档变更"与"应用镜像目录文件变更"，将根目录 `README.md` 误判为镜像发布相关文件并报告 `[Path Error]`。此问题需在 CI 工具侧修复，不属于 PR 提交者的可控范围。

## 潜在风险
无。未对任何文件进行修改，不存在引入新问题的风险。