# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**：CI 流水线的 appstore 发布规范预检工具 (`eulerpublisher/update/container/app/update.py`) 错误地将根级 `README.md` 纳入路径校验范围，导致误报 `Path Error`。该文件属于项目级文档，不应参与 appstore 镜像发布路径校验。

## 修改的文件
无。PR 仅修改了 `README.md` 的文档内容（新增 tag 条目、修正链接），该变更无任何错误，CI 失败源于基础设施层的校验逻辑缺陷。

## 修复逻辑
分析报告定性为 `infra-error`，根因在 CI 校验工具 `update.py` 的路径过滤逻辑缺失，而非 PR 修改的 `README.md` 内容问题。按照规范要求，infra-error 不应强行修改代码以绕过 CI 检查。实际修复不在当前 PR 范围内——需要由 CI 基础设施维护者：
1. 在 `update.py` 中为根级 `README.md` 添加白名单/跳过逻辑
2. 或配置 appstore release pipeline 跳过仅含文档变更的 PR

## 潜在风险
无。当前未修改任何文件。