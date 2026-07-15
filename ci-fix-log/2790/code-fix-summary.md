# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认失败类型为 `infra-error`，根因是 CI 编排工具 `eulerpublisher/update/container/app/update.py:273` 的 appstore 路径校验逻辑存在 bug：对仓库根目录的 `README.md` 报 `[Path Error]`，声称期望路径为 `/README.md`，但该文件实际就在仓库根目录，路径完全正确。PR #2790 仅修改了 `README.md` 中的镜像 Tag 列表文本（新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目），属于纯文档类改动，不涉及任何 Dockerfile、构建逻辑或元数据文件。CI 工具对根目录 README.md 的路径误报与 PR 实际内容无关。

此问题需要由 CI 工具维护方修复 `eulerpublisher` 仓库中 appstore 路径校验的实现逻辑，而非修改本仓库代码。

## 潜在风险
无（未对源码做任何修改）