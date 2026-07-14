# 修复摘要

## 修复的问题
无需代码修改。CI 失败是由 appstore 发布规范预检工具（eulerpublisher）误报导致，该工具对根目录级纯文档变更（`README.md`）执行了镜像发布路径校验，属于 CI 基础设施误报（infra-error）。

## 修改的文件
无。PR 仅修改了 `README.md`（根目录文档），内容为更新基础镜像可用 tags 列表，属于纯文档变更，不涉及任何镜像构建或发布，不应受 appstore 路径校验约束。

## 修复逻辑
根据 CI 失败分析报告，失败根因位于 `eulerpublisher/update/container/app/update.py:273`，eulerpublisher 的路径校验逻辑未正确处理根目录级文档文件变更的场景。本 PR 变更内容（`README.md` / `README.en.md` 中的 tags 列表更新）完全正确，CI 检查工具不应将根目录文档纳入 appstore 镜像发布路径校验范围。此问题需由 CI 流水线维护方修复 eulerpublisher 工具或调整触发条件，PR 代码本身无需任何修改。

## 潜在风险
无。`README.md` 内容变更仅限于更新文档中的镜像 tags 列表，不影响任何构建或发布逻辑。