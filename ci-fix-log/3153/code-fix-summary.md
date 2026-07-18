# 修复摘要

## 修复的问题
无需代码修改 — CI 失败属于基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无（无需修改任何源码文件）

## 修复逻辑
CI 失败来自 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范检查器。该检查器对仓库根目录的 `README.md` 执行了路径格式校验，期望路径格式为 `/README.md`（绝对路径），但 diff 中检测到的变更文件路径为 `README.md`（相对路径），导致路径校验失败。

仓库根级的 `README.md` 是仓库级文档，不属于任何 appstore 镜像目录，不应受 appstore 路径规则约束。CI 检查器未能区分仓库级文档和 appstore 镜像文档，将路径格式差异误报为规范错误。

**这不是 PR 代码侧能够修复的问题**，需要 CI 维护方在 `eulerpublisher` 工具中修正路径校验逻辑：将仓库根目录文件（如根 `README.md`、`README.en.md`、`LICENSE` 等）从 appstore 路径校验中排除，或对 diff 文件列表做路径归一化处理。

## 潜在风险
无