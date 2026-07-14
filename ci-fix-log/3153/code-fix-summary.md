# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：EulerPublisher 的 appstore 预检工具（`update.py`）将根级文档 `README.md` 的变更误判为 appstore 上架请求，并按 appstore 路径规范（`{category}/{image-version}/{os-version}/`）进行校验导致误报。**本仓库代码无误，无需修改。**

## 修改的文件
无。PR 修改的 `README.md` 内容正确（更新基础镜像 tag 列表），且 `README.en.md` 已在之前的修复提交中回退。

## 修复逻辑
CI 分析报告指出本次失败属于 **infra-error**：根因在于外部 CI 工具 `eulerpublisher/update/container/app/update.py`（不在本仓库中）缺少对纯文档变更 PR 的跳过逻辑。该工具将所有 PR 变更文件（包括根级 `README.md`）均视为 appstore 上架候选进行路径校验，导致误报 `[Path Error] The expected path should be /README.md`。

PR #3153 仅更新根级文档中的基础镜像 tag 列表，不涉及任何 Dockerfile 或镜像目录变更。代码本身无 bug，修复应在 CI 工具层面进行（在 `update.py` 中增加判断：若 PR 变更文件全部为根级非镜像目录文件则跳过 appstore 校验）。

## 潜在风险
无。本仓库代码未做任何修改，不影响任何功能。