# 修复摘要

## 修复的问题
**无需代码修改**。CI 失败为 infra-error，根因是 eulerpublisher 工具的 appstore 发布规范预检脚本（`update.py:273`）对仓库根目录 README.md 的路径校验逻辑存在缺陷（可能对 git diff 输出的路径前缀如 `a/` 与期望的 `/README.md` 进行了过于严格的字符串比对），导致误报 FAILURE。PR #2790 仅包含合法的文档维护操作（在 README.md 中新增可用镜像 Tags 条目 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2`），与 CI 失败无关。

## 修改的文件
- 无（infra-error，无需修改 PR 代码）

## 修复逻辑
CI 分析报告明确判定该失败为 infra-error，置信度中，失败位置在 CI 基础设施工具 eulerpublisher 内部，而非本仓库的任何文件。PR 的变更文件（README.md）内容正确，无需任何改动。此问题应由 CI 团队修复 eulerpublisher 的路径比对逻辑，或添加"仅 README 变更"跳过 appstore 检查的豁免规则。

## 潜在风险
无（未修改任何代码）