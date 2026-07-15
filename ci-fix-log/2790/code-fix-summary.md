# 修复摘要

## 修复的问题
无法修复——CI 失败根因位于 `eulerpublisher/update/container/app/update.py`（CI 基础设施工具），不在 PR 变更文件范围内。PR 仅修改了 `README.md` 文档，不涉及任何容器镜像发布内容，但 CI 的 appstore 发布规范检查仍然运行，对从 git diff 提取的路径 `README.md`（缺少前导 `/`）与预期路径 `/README.md` 做比对时失败。

## 修改的文件
无代码修改。PR 仅变更了 `README.md`，而修复需改动 `eulerpublisher/update/container/app/update.py`（路径归一化逻辑）或 CI 编排配置，均不在 `pr.changed_files` 列表内。

## 修复逻辑
该 CI 失败属于基础设施问题（infra-error），不是 PR 代码本身有 bug。根因有两个层面：
1. **路径格式问题**：`eulerpublisher` 工具从 git diff 中提取文件路径后未添加前导 `/`，导致 `README.md` 与预期 `/README.md` 不匹配。
2. **检查触发范围问题**：PR 仅包含纯文档变更（`README.md`、`README.en.md`），不应触发 appstore 发布规范检查。

两个修复方向（路径归一化 / 跳过纯文档 PR 的检查）都需要修改 CI 工具代码，超出了本次代码修复的范围。

## 潜在风险
无——未对源码仓库做任何修改。