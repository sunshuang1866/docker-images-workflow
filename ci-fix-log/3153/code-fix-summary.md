# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范检查器对根级文档文件（`README.md`）进行了不合理的路径校验，导致纯文档 PR 被错误拒绝。本 PR 的代码变更本身无问题，无需修改源码。

## 修改的文件
无。此失败属于 CI 基础设施层面（`eulerpublisher/update/container/app/update.py`）的检查逻辑缺陷，不应通过修改源码仓库来解决。

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因是 CI 的 appstore 规范检查器未区分"根级非镜像文件"与"appstore 镜像目录文件"，对所有变更文件一刀切地进行路径校验。PR #3153 仅修改了 `README.md`（更新基础镜像 tag 列表），不涉及任何 appstore 镜像目录，不应被 appstore 路径规范约束。

修复应在 CI 工具侧（eulerpublisher）进行，使其只对 appstore 镜像目录下的文件进行路径校验，或为纯文档类 PR 提供豁免机制。

## 潜在风险
无。未对源码仓库做任何修改，不影响任何功能。