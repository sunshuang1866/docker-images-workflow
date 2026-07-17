# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，根因是 CI 工具 `eulerpublisher` 的 appstore 预检逻辑将根级文档文件 `README.md` 错误地纳入镜像路径格式校验，与 PR 代码无关。

## 修改的文件
- 无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`（置信度：中）。PR #2790 仅修改了根级 `README.md`（更新镜像 Tags 列表），属于纯文档变更。CI 工具 `eulerpublisher` 的 appstore 预检阶段对所有变更文件无条件执行 `{image-version}/{os-version}/Dockerfile` 格式校验，`README.md` 不匹配该模式导致校验返回 FAILURE。这是 CI 基础设施工具的缺陷，不是 PR 代码的问题，无需在源码库中进行任何代码修改。

## 潜在风险
无 — 未修改任何源码文件。