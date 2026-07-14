# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，由 appstore 发版校验管线对所有 PR 统一执行路径检查导致，该检查不适用于纯文档类 PR。

## 修改的文件
无

## 修复逻辑
本次 PR 仅修改了根目录的两个 README 文件（`README.md`、`README.en.md`），更新基础镜像 Tag 列表，不涉及任何应用镜像 Dockerfile、meta.yml 或 image-list.yml。CI 失败的根本原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验工具对所有 PR 变更文件执行应用镜像目录结构检查，将根级文档文件 `README.en.md` 标记为"期望路径应为 /README.md"，`README.md` 虽位置正确也报错（疑为校验工具固定模板行为）。此问题属于 CI 基础设施缺陷，需在 CI 编排层（trigger job）或 `update.py` 中添加分流逻辑：当 PR 仅修改根级文档文件时跳过 appstore 路径校验。

## 潜在风险
无