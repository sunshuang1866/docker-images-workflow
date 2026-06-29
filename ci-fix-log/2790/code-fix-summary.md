# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：CI 流水线将纯文档 PR（仅修改仓库级 README）误纳入 appstore 发布规范校验流程，导致路径校验失败。PR 变更内容本身无问题。

## 修改的文件
无

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`，根因在 CI 基础设施代码 `eulerpublisher/update/container/app/update.py:273` 中缺少对纯文档 PR 的识别和过滤逻辑。PR #2790 仅修改了 `README.en.md` 和 `README.md`（更新支持的 Tags 列表），属于纯文档维护，不涉及任何容器镜像构建或发布。该修复需由 CI 团队在 `update.py` 中增加跳过机制，非源码仓库内文件可解决。

## 潜在风险
无