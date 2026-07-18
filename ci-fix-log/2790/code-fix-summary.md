# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），非 PR 代码变更所致。

## 修改的文件
无

## 修复逻辑

CI 失败分析报告将此失败分类为 **infra-error**（置信度：中）。根因是 CI 编排工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布预检逻辑将仓库根目录的 `README.md` 错误地纳入了镜像目录路径校验。PR #2790 仅修改了 `README.md` 文档内容（更新镜像 Tags 列表），不涉及任何 Dockerfile、镜像构建或 appstore 发布相关文件，该 CI 检查本不应触发。

此问题需在 CI 基础设施侧修复（例如在 `update.py` 中增加过滤条件，跳过仓库根目录及非镜像目录的文件），而非修改 PR 涉及的源码文件。由于当前修复上下文仅允许修改 `README.md`，且 `update.py` 不在可修改文件列表中，无法在本次修复中进行代码变更。

## 潜在风险
无 — 未对任何源文件进行修改。