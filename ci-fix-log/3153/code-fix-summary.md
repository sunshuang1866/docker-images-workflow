# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），appstore 校验 pipeline 对纯文档 PR（仅修改 `README.md`）进行了不应有的应用镜像路径校验，导致误报 FAILURE。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`，根因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范校验工具将根级文档文件 `README.md` 错误地归类为应用镜像发布内容进行路径校验。PR 的文档变更本身（更新基础镜像可用 Tags 列表）没有任何内容错误。这不是源代码层面的问题，应通过修改 CI 编排逻辑（在路径校验前过滤根级文档文件）或调整 CI trigger 条件来解决，而不是修改 `README.md`。

## 潜在风险
无——未修改任何代码文件。