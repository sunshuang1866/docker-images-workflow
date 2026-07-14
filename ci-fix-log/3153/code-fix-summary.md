# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施层面的误报（infra-error），PR #3153 仅修改了仓库根目录的 README.md（文档更新），不涉及任何应用镜像变更。CI 的 appstore 预检工具错误地将根目录 README.md 纳入了应用镜像 README 路径校验范围，导致误报 FAILURE。

## 修改的文件
无

## 修复逻辑
根据 CI 分析报告，失败类型为 `infra-error`，根因是 CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）的检查逻辑缺陷——未排除仓库根目录级别的 README.md/README.en.md 文件，导致文档 PR 被错误拦截。PR 的文档修改内容本身正确，无需任何代码改动。

应由 CI 维护者调整 appstore 预检逻辑，排除仓库根目录文档文件（路径为 `/README.md` 和 `/README.en.md`），不将其纳入 appstore 镜像 README 路径校验范围。

## 潜在风险
无