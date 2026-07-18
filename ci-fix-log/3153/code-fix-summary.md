# 修复摘要

## 修复的问题
无需代码修改 — CI 失败属于基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定该失败为 `infra-error` 类型。CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）在扫描 PR 变更文件时，对仓库根目录的 `README.md`（项目主文档）产生路径校验误报——该工具将此文件当作需要符合 appstore 发布路径规范的应用镜像 README 进行校验，导致 `[Path Error]` 误报。

PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的基础镜像可用 Tags 列表，属于纯文档变更，不涉及任何应用镜像 Dockerfile、meta.yml、image-info.yml 或 image-list.yml。该 CI 失败并非 PR 代码变更引入的问题，无法通过修改 PR 涉及的源文件解决。

修复应在上游 CI 基础设施代码（`eulerpublisher` 仓库的 `update.py`）中进行：对位于仓库根目录且不属于任何应用镜像目录（如 `AI/`、`Bigdata/`、`Database/` 等）的文件，跳过 appstore 路径规范校验。

## 潜在风险
无 — 未修改任何源文件。