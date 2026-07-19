# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。CI 工具 eulerpublisher 的 appstore 发布规范检查器对根目录 `README.md` 文件报告了 `Path Error`，其路径比较逻辑存在前导 `/` 匹配不一致的 bug（提取的路径 `README.md` 与期望路径 `/README.md` 不匹配），属于 CI 层面缺陷。

## 修改的文件
无（无需代码修改）

## 修复逻辑
- PR #3153 仅修改了 `README.md` 的文档内容（更新可用基础镜像标签列表），不涉及任何文件路径变更或元数据文件修改。
- CI 失败原因为 eulerpublisher 的路径校验逻辑 bug，与 PR 变更无关。
- 此为 CI 基础设施问题，需由 CI 平台维护团队修复 eulerpublisher 的路径比较逻辑，或调整 appstore 发布规范检查的触发范围（对仅修改根目录文档的 PR 不应执行该检查）。
- 在本仓库范围内无需且不应进行任何代码修改。

## 潜在风险
无