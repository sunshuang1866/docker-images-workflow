# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），由 CI 工具 `eulerpublisher` 的 appstore 校验逻辑误将根级文档文件 `README.md` 纳入镜像路径校验导致。

## 修改的文件
无（infra-error，无需修改源码）

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因是 `eulerpublisher/update/container/app/update.py` 工具在校验 appstore 镜像路径时，错误地对仓库根目录的纯文档文件 `README.md` 执行了校验并报告 FAILURE。PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的镜像 tag 列表，不涉及任何 Dockerfile 或镜像构建逻辑，不属于需要 appstore 路径校验的范围。

根据修复原则，对于 `infra-error` 类型的失败，不应强行修改源码代码来绕过 CI 问题。此问题需要在 CI 工具 `eulerpublisher` 侧修复——在校验流程中增加文件路径过滤，将仓库根目录的 `README.md` / `README.en.md` 等纯文档文件排除在 appstore 路径校验范围之外。

## 潜在风险
无（未修改任何代码）