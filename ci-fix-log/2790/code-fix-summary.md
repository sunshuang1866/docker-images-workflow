# 修复摘要

## 修复的问题
CI 预检工具 `eulerpublisher` 的 appstore 发布规范校验错误地将仓库根级 `README.md` 纳入镜像路径校验，导致纯文档变更的 PR 被标记为 FAILURE。此问题属于 CI 基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无代码修改。PR 仅涉及根级 `README.md` 的基础镜像 Tags 列表文档更新，内容本身正确，无需改动。

## 修复逻辑
CI 分析报告指出两种可能根因：
1. CI 工具未能跳过仓库根级非镜像文件（方向 1）
2. CI 工具的路径规范化存在 bug，未正确处理 git diff 路径前缀（方向 2）

二者均属于 `eulerpublisher/update/container/app/update.py` 中的 CI 工具问题，与 `README.md` 的文件内容无关。根级 `README.md` 是纯文档文件，不属于任何应用镜像目录结构，其内容修改不应触发镜像路径校验。根据分析报告结论，本失败属于 infra-error，无需对 `pr.changed_files` 中的文件做任何代码修改。

## 潜在风险
无。未修改任何源文件，不会引入新问题。CI 工具侧需要 `eulerpublisher` 维护者修复对根级非镜像文件的路径校验逻辑。