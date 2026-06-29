# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 **infra-error**（基础设施误报），PR #2790 仅包含 `README.md` / `README.en.md` 文档更新，CI 的 appstore 发布规范预检工具 (`update.py`) 对所有 PR 统一执行发布路径校验，但缺少对纯文档类 PR 的跳过逻辑，导致误报 "Path Error"。

## 修改的文件
无。`README.md` 和 `README.en.md` 的文档内容本身正确，无需改动。

## 修复逻辑
分析报告明确分类为 `infra-error`，置信度中等。根因是 CI 流水线中 `update.py:273` 的路径校验逻辑不区分文档类变更与镜像构建类变更，导致纯 README 更新的 PR 被错误拦截。此问题需由 CI 管理员在 Jenkins 侧手动 bypass 或通过流水线配置（如 PR 标签、路径过滤）跳过 appstore 检查，不属于源代码层面的可修复问题。

## 潜在风险
无——两个 README 文件的文档更新内容正确，与本次 CI 失败无因果关系。