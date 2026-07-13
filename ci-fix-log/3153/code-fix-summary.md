# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error）：`eulerpublisher` 仓库的 `update.py` 脚本对 PR 所有变更文件执行 appstore 路径规范校验，根目录文档文件 `README.md` / `README.en.md` 因不匹配镜像目录路径模式（如 `{image-version}/{os-version}/Dockerfile`）而被误报为 `Path Error`。

## 修改的文件
无（本仓库代码无需修改）。

## 修复逻辑
- CI 校验工具（`eulerpublisher/update/container/app/update.py`）位于 `eulerpublisher` 外部仓库，不在本仓库管理范围内。
- PR #3153 仅更新了根目录文档文件中的基础镜像 tag 列表，内容正确，不涉及任何 Dockerfile 或镜像构建文件。
- 根因是 CI 脚本的文件遍历逻辑未排除非镜像目录下的文件，导致纯文档 PR 被错误拦截。
- 正确修复应在上游 `eulerpublisher` 仓库的 `update.py` 中添加文件过滤逻辑，排除根目录级文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等）使其不受 appstore 路径规范约束。
- 本仓库的 `pr.changed_files` 仅包含两个 README 文档文件，无法通过修改这些文件解决 CI 基础设施层面的问题。

## 潜在风险
无。本仓库代码未做任何修改，不存在引入新问题的可能。CI 基础设施修复需在上游 `eulerpublisher` 仓库单独进行。