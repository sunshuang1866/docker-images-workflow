# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error）：`eulerpublisher` 工具对纯文档变更 PR（仅修改 `README.md`）错误地触发了 appstore 上架规范校验。

## 修改的文件
无（infra-error，不涉及源码修改）

## 修复逻辑
分析报告明确指出该失败类型为 `infra-error`，失败原因与 PR 变更内容无直接关联。本次 PR（#2790）仅更新了 `README.md` 中的"可用镜像的 Tags"列表，属于纯文档更新。CI 流水线中的 `eulerpublisher` 工具未对纯文档变更 PR 进行过滤，导致在文档文件上执行了不适用于文档文件的 appstore 路径规范性校验，从而产生误报。

此问题需要由 CI 流水线维护方在 `eulerpublisher/update/container/app/update.py` 中增加对文档类 PR 的跳过逻辑，或在 CI 配置中增加条件判断。这些修改不在当前 PR 的变更范围之内，也无法通过对 `README.md` 文件本身做任何改动来解决。

## 潜在风险
无