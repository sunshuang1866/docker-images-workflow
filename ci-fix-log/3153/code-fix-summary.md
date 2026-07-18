# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），`eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范校验将仓库根目录的 `README.md` 错误纳入了镜像路径校验流程，而 PR #3153 对 `README.md` 的修改仅为纯文档更新（新增基础镜像 Tags 条目），文件内容和路径均正确。

## 修改的文件
无。`README.md` 的内容变更正确无误，不需要任何修改。

## 修复逻辑
CI 失败根因在于 `eulerpublisher/update/container/app/update.py` 的 diff 文件过滤逻辑未将仓库根目录级别的通用文档（如 `/README.md`）排除在 appstore 路径校验之外。该校验旨在检查镜像子目录内的 `README.md` 路径规范，不应作用于根级项目说明文档。由于 `update.py` 不在 PR 变更文件列表（`pr.changed_files`）中，且问题属于 CI 工具本身的范围，应在 CI 工具侧修复过滤逻辑，无需修改本仓库的任何源代码。

## 潜在风险
无。`README.md` 未做任何修改，不影响其他功能。