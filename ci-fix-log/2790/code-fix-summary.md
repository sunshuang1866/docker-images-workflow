# 修复摘要

## 修复的问题
无需代码修复 — CI appstore 发布规范检查将根级 `README.md` 文档修改错误地标记为路径校验失败，属于 CI 基础设施假阳性（infra-error）。

## 修改的文件
无

## 修复逻辑
PR #2790 仅修改了仓库根目录的 `README.md`（更新基础镜像 Tags 列表），属于纯文档维护，不涉及任何应用镜像的 Dockerfile、meta.yml、image-list.yml 或 image-info.yml。CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）未能区分根级文档变更与应用镜像目录变更，将 `README.md` 错误地纳入 appstore 路径校验范围，导致路径不合规报错。该问题已被分析报告标记为 `infra-error`（置信度：高），无需修改 PR 代码。CI 工具侧需增强过滤逻辑以排除根级非应用镜像文件。

## 潜在风险
无