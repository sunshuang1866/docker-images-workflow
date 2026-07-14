# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），根因是 CI 工具 `eulerpublisher/update/container/app/update.py` 内部路径校验逻辑不一致：diff 模块输出路径为 `README.md`（无前导 `/`），但校验模块期望 `/README.md`（带前导 `/`），与 PR #3153 的文档内容变更无关。

## 修改的文件
无。

## 修复逻辑
该 CI 失败是 CI 基础设施的路径校验 bug，不属于源码层面可修复的问题。PR #3153 仅更新了 `README.md` 中的基础镜像 tags 列表，文件内容正确，无需任何代码改动。此问题需要由 CI 团队修复 `update.py` 中的路径处理逻辑（统一加或不加前导 `/`），或调整 CI pipeline 触发条件，使纯文档 PR 不进入 appstore 发布规范校验流程。

## 潜在风险
无。