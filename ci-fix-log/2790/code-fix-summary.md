# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error（CI 基础设施问题）：CI 流水线触发器将仅修改 README.md 的纯文档 PR 错误地送入 appstore 发布规范校验器（`update.py`），导致校验器误报 `[Path Error]`。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，置信度中。根因是 CI 触发器（`multiarch/openeuler/trigger/openeuler-docker-images`）在下游 job 调度时未根据 PR 变更文件类型进行过滤，纯文档更新 PR 被错误地路由到 appstore 发布规范校验流程。此问题属于 CI 基础设施层面，不在源码仓库代码范围内，不需要也不应对 README.md 或任何源码文件进行修改。

## 潜在风险
无（源码无变更）。建议在 CI 触发器层增加文件变更过滤逻辑：当 PR 仅包含根目录文档变更且不含应用镜像目录变更时，跳过 appstore 规范校验 job。