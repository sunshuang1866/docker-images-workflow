# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 eulerpublisher 工具的 appstore 发布规范预检逻辑错误地将根层级 `README.md` 纳入校验范围引起，与 PR 代码内容无关。

## 修改的文件
无（无需修改 PR 文件）

## 修复逻辑
PR #2790 仅更新了根目录 `README.md` 的文档内容（基础镜像 Tags 列表），属于纯文档变更，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml 文件。CI 的 eulerpublisher 工具在 appstore 发布规范预检时，错误地对根层级 README 文件执行了路径格式校验（期望 `/README.md` 而非 `README.md`），该预检本应仅针对 `{category}/{image}/{version}/{os-version}/` 目录树下的应用镜像文件执行。根据分析报告结论，根因在 CI 基础设施（eulerpublisher 工具）而非 PR 代码，无需对 `README.md` 做任何代码修改。

## 潜在风险
无。不涉及代码变更。