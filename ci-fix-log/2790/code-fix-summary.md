# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施误判（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认 PR #2790 仅修改了根级文档文件 `README.md` 和 `README.en.md`，属于纯文档更新。CI 的 appstore 规范预检工具（`eulerpublisher/update/container/app/update.py`）对不涉及任何应用镜像目录的纯文档 PR 错误执行了面向应用镜像发布场景的路径校验规则，导致 `README.md` 被误判为路径不合规。此失败与 PR 实际代码变更无关，属于 CI 基础设施配置问题，应由 CI 工具侧在预检阶段增加前置过滤（排除不含应用镜像目录变更的 PR），而非修改源码仓库中的文件。

## 潜在风险
无