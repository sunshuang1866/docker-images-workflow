# 修复摘要

## 修复的问题
无需代码修复 — CI 失败属于基础设施错误（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认失败类型为 `infra-error`，置信度低。失败原因是 CI 流水线中的 `eulerpublisher` 工具对仓库根目录的 `README.md` 进行了 appstore 发布规范路径校验，错误地报告 `[Path Error] The expected path should be /README.md`，但该文件确实位于仓库根目录 `/README.md`，错误信息与实际情况矛盾。

本 PR 仅修改了两个文档文件（`README.md` 和 `README.en.md`），内容为更新镜像版本列表，未涉及任何 Dockerfile、meta.yml、image-list.yml 等镜像发布相关文件。CI 失败与 PR 的文档内容变更无直接关联，根源在于 `eulerpublisher` 工具无法正确处理仅包含根目录文档变更的 PR。

根据修复规范：分析报告指出为 `infra-error`，无需对源代码进行修改，不应强行改代码来绕过 CI 基础设施问题。

## 潜在风险
无 — 未修改任何文件。