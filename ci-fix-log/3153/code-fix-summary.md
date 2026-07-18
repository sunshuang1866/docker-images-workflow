# 修复摘要

## 修复的问题
无代码修改。CI 失败为 `infra-error`（基础设施错误），与 PR 代码变更内容无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`。失败原因是 CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）将仓库根目录的文档文件 `README.md` 纳入了应用镜像发布规范检查范围，并因路径格式差异报错。本次 PR 仅修改了 `README.md` 中的基础镜像 Tags 列表文档内容，不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建文件，本身不应触发 appstore 检查流程。

该问题根因在 CI 工具侧（`eulerpublisher/update/container/app/update.py`），需要对根级非应用镜像文件做豁免过滤。该文件不在 PR 的 `changed_files` 列表中，也无法通过修改 `README.md` 代码来绕过 CI 检查。此错误属于 CI 基础设施边界处理缺陷，需由 CI 工具维护方修复。

## 潜在风险
无