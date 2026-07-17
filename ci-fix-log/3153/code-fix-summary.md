# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 **infra-error**，根因在 CI 基础设施工具（eulerpublisher `update.py`）的路径比较逻辑缺陷，与 PR 代码变更无关。

## 修改的文件
无。PR 仅修改了 `README.md`（更新基础镜像可用 tags 的文档信息），该文件本身不存在需要修复的问题。

## 修复逻辑
CI 分析报告明确指出：失败由 eulerpublisher 的 appstore 发布规范预检工具（`update.py:273`）在处理 `git diff --name-only` 输出的文件路径时未做路径规范化导致——工具期望绝对路径 `/README.md`，但 `git diff` 输出相对路径 `README.md`，字符串比较不匹配。这是一个 CI 基础设施层面的 bug，应由 CI 维护者修复 `update.py` 中的路径比较逻辑（统一添加或去除前导 `/`）。PR 仅更新了根目录下的 README 文档文件，未涉及任何 Dockerfile 或镜像元数据变更，该 CI 检查本不应阻塞此 PR。

## 潜在风险
无——本次未对任何源代码文件做修改。