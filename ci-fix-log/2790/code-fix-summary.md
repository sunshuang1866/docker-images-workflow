# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施问题（false positive）。

## 修改的文件
无

## 修复逻辑

CI 失败根因是 CI 预检工具 `eulerpublisher/update/container/app/update.py` 在扫描 PR 变更文件时，将仓库根目录的 `README.md`（项目级整体说明文档）错误地纳入了 appstore 镜像 README 规范校验，导致 `[Path Error] The expected path should be /README.md`。

根目录 `README.md` 是仓库整体说明文档，其内容结构和存放路径与 appstore 要求的镜像级 README（`{category}/{image}/{version}/README.md`）完全不同，不应受 appstore 发布规范约束。

**正确的修复位置**：CI 工具 `update.py` 中的文件过滤逻辑需要增加对仓库根目录 README 文件的排除规则（如 `README.md`、`README.en.md`），而非在 `README.md` 中做任何修改。

**当前 PR 可修改范围限制**：`pr.changed_files` 仅包含 `README.md`，无法触及 CI 编排工具代码。根据"修复原则"中关于 infra-error 的规定，此场景下无需对源码做任何代码修改。

## 潜在风险
无 — 未对代码做任何修改，不影响任何功能。该错误需由 CI 团队在 `eulerpublisher` 工具的 `update.py` 中修复。