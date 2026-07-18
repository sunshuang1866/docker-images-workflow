# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于基础设施错误（infra-error），CI 工具 `eulerpublisher` 的 appstore 预检逻辑错误地将纯文档文件 `README.md` 纳入了镜像发布规范校验范围，导致误报 FAILURE。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-list.yml 等镜像构建相关文件。CI 的 `eulerpublisher/update/container/app/update.py` 在扫描变更文件差异后，未能过滤仓库根目录的 `.md` 文档文件，将其错误地纳入 appstore 发布规范预检，导致路径格式校验失败。此问题根源在 CI 工具侧，不在本 PR 的源代码范围内，无需且不应修改任何源码文件。

## 潜在风险
无。本次不改动任何代码。