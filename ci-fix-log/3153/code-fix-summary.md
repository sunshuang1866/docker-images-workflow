# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题（infra-error），非源代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 **infra-error**，根因在 CI 流水线设计：

- PR #3153 仅修改了仓库根级的 `README.md` 和 `README.en.md`，属于纯文档更新，变更本身合法。
- CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）将这两个根级文档文件纳入镜像路径校验流程，但它们不在 appstore 镜像目录结构（`{分类}/{镜像}/{版本}/{系统版本}/`）中，校验工具无法将其映射到合法镜像路径，导致误报路径错误。
- 根因在 CI 流水线：对所有 PR（包括纯文档 PR）均运行 appstore 发布规范预检，仓库根级文档文件无豁免机制。

**修复方向**（需 CI 流水线侧配合）：
1. CI 流水线跳过纯文档 PR 的 appstore 发布规范预检。
2. 或在 `eulerpublisher` 工具中为仓库根级文件（`README.md`、`README.en.md` 等）增设白名单/豁免逻辑。

按照修复工程师工作规范：infra-error 类型失败不应对源代码做任何修改。

## 潜在风险
无 — 未修改任何源代码文件。