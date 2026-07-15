# 修复摘要

## 修复的问题
CI 失败为基础设施错误（infra-error），与 PR 代码无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出该失败是 `eulerpublisher` 工具在 appstore 发布规范预检阶段的路径比对逻辑缺陷引起的。该工具将 `git diff` 输出的 `README.md`（不含前导 `/`）与期望路径 `/README.md`（含前导 `/`）做字符串精确匹配，因路径格式不一致导致比对失败。该 PR (#3153) 仅修改了位于仓库根目录的 `README.md` 和 `README.en.md`，属于纯文档更新，文件位置本身正确。此问题应由 CI 维护团队修复 `eulerpublisher/update/container/app/update.py` 中的路径规范化逻辑，PR 代码侧无需任何改动。

## 潜在风险
无