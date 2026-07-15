# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施误将纯文档 PR（更新 README.md 中的基础镜像 tags 列表）路由到 appstore 发布规范校验流程，导致不相关的 "Path Error" 检查失败。

## 修改的文件
无（无需修改任何源码文件）

## 修复逻辑
本 PR (#3153) 仅修改了根级 `README.md`，更新了"可用镜像的Tags"列表，属于纯文档变更，不涉及任何 Dockerfile、构建脚本或 appstore 应用镜像元数据。CI 工具 (`eulerpublisher/update/container/app/update.py`) 在处理此 PR 时错误地将根级 `README.md` 视为 appstore 应用镜像条目进行检查，触发了 "Path Error: The expected path should be /README.md" 校验失败。根级 README 是仓库通用文档，不应被纳入 appstore 发布规范检查范围。此问题需由 CI 维护团队在 appstore 检查逻辑中添加对根级 `README.md` 的过滤/白名单机制来解决，code-fixer 侧无需对 PR 内容做任何修改。

## 潜在风险
无 — 未修改任何代码，不会引入新问题。