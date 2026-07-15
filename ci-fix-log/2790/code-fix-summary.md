# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）。PR #2790 为纯文档变更（更新 README.md 中可用镜像 Tags 列表），不涉及任何应用镜像发布文件。CI 流水线中的 `eulerpublisher` 工具错误地将根级 README.md 纳入 appstore 发布规范校验，导致 `[Path Error] The expected path should be /README.md` 校验失败。该问题根因在 CI 工具/流水线配置，不在 PR 变更的源文件中。

## 修改的文件
无。此 CI 失败属于基础设施问题，在 `README.md` 中无法通过代码修改解决。

## 修复逻辑
CI 失败分析报告明确指出根因位于 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范校验逻辑，该校验未区分"纯文档变更"与"应用镜像发布"，对所有 diff 中的文件均执行应用镜像路径规范检查。PR 仅修改了根级 `README.md` 和 `README.en.md`（更新 Tags 列表），不含任何 `{类别}/{镜像名}/{版本}/{OS版本}/Dockerfile` 等应用镜像目录文件，因此不应触发 appstore 校验。

正确的修复方向为：在 CI 编排层（Jenkins pipeline 配置）或 `eulerpublisher` 工具中增加判断逻辑，当 PR diff 仅包含根级文档文件（`README.md`、`README.en.md` 等）且不含任何应用镜像目录文件时，跳过 appstore 发布规范检查。此变更不在 `pr.changed_files` 范围内，无需修改 PR 源文件。

## 潜在风险
无。`README.md` 文件无需任何代码改动，当前失败为 CI 工具配置问题，不影响代码正确性。