# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error），无需对 PR 代码做任何修改。

## 修改的文件
无

## 修复逻辑
CI 失败根因为 `eulerpublisher/update/container/app/update.py` 工具在处理 diff 路径时存在前导 `/` 不一致问题——diff 返回的路径为 `README.md`（无前导 `/`），而校验逻辑期望绝对路径 `/README.md`。同时该工具将仓库根目录的纯文档文件误纳入 appstore 发布规范校验流程。PR #3153 仅修改了 `README.md` 的文本内容（更新可用基础镜像 Tags 列表），属于纯文档修改，与 CI 失败完全无关。

该问题需要在 CI 工具自身中修复（过滤非应用镜像目录文件或统一路径格式），不属于本 PR 代码修复范围。

## 潜在风险
无