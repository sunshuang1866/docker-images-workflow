# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`（基础设施误报），非 PR 代码问题。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：失败类型为 `infra-error`，根因在于 CI 编排工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检逻辑存在路径比对缺陷——将 `git diff --name-only` 输出的 `README.md`（无前导 `/`）与期望路径 `/README.md`（有前导 `/`）进行字面比较，因前导 `/` 不匹配而误判 FAILURE。实际上 `README.md` 始终位于仓库根目录 `/README.md`，路径完全正确。

此 PR 仅修改了 `README.md` 的文档内容（更新可用基础镜像 tags 列表），未新增、删除、移动或重命名任何文件。CI 失败与 PR 变更无关，属于 CI 工具 bug，需由 CI 平台维护者修复 `update.py` 中的路径规范化/比对逻辑。Code Fixer 无需对 PR 代码做任何修改。

## 潜在风险
无