# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为 `infra-error`（CI 基础设施问题）。

## 修改的文件
无。PR #2790 仅修改了仓库根目录的文档文件 `README.md`（及 `README.en.md`），这些文件不包含 Dockerfile、`meta.yml` 或 `image-list.yml`，不应被 appstore 镜像发布校验所覆盖。CI 的 `eulerpublisher` 工具将根级纯文档文件误纳入 appstore 发布校验流程，导致 `Path Error`。

## 修复逻辑
分析报告将此次失败归类为 `infra-error`，根因在于 CI 流水线或 `eulerpublisher` 工具未排除仓库根目录的纯文档文件。修复应在 CI 配置或 `eulerpublisher` 工具源码中调整，无需对 Docker 镜像仓库内的文件做任何变更。根据任务约束中的规则——"如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"，本次不执行任何代码修改。

## 潜在风险
无。不涉及代码变更，不会引入回归风险。CI 侧的修复需要在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中增加对根级非镜像文件的排除规则。