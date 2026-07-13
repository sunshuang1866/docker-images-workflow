# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：纯文档 PR 被 appstore 发布规范路径校验拒绝。

## 修改的文件
无。当前 PR 涉及的文件（`README.md`、`README.en.md`）均为正确的文档更新，本身无需修改。

## 修复逻辑
该失败属于 CI 基础设施问题，非源码问题。根因在 `eulerpublisher/update/container/app/update.py:273`：该文件的 appstore 路径规范校验对所有 PR 强制要求变更文件符合 Docker 镜像发布路径格式（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），但缺少对纯文档类 PR 的跳过逻辑。README 文件不在此路径规范内，因此被判定为 Path Error。

分析报告指出这是 infra-error 类型，正确的修复应在 CI 流水线层面添加判断逻辑：当 PR 变更文件全部为非 Dockerfile 的文档文件时，跳过 `update.py` 的 appstore 路径校验步骤。这超出了当前 PR 允许修改的文件范围，源代码无需改动。

## 潜在风险
无。源代码层面未做任何修改。