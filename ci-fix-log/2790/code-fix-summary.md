# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 预检将仓库根目录的 `README.md` / `README.en.md` 视为应用镜像文件进行校验，实际 PR 仅更新了文档内容，不涉及任何应用镜像变更。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告将其定性为 **infra-error**（CI 基础设施问题）。失败根因在 `eulerpublisher/update/container/app/update.py` 中缺少对仓库根层级 README 文件的过滤逻辑，该文件不在原始 PR 的 `changed_files` 范围内（`['README.en.md', 'README.md']`），且根据修复约束，infra-error 类型无需对源代码进行修改。

PR #2790 仅更新了 `README.md` 和 `README.en.md` 中的镜像 Tag 文档信息（添加 24.03-lts-sp3、25.09 等新 Tag 条目链接），这些是仓库级文档，不涉及任何 Dockerfile、meta.yml 或 image-list.yml，不应触发 appstore 路径预检。此失败与 PR 变更内容无关，属于 CI 流程对非应用镜像文件变更的误报。

## 潜在风险
无 — 无需代码修改。