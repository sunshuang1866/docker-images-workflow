# 修复摘要

## 修复的问题
无需代码修改 — **infra-error**。CI 流水线的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对纯文档类 PR 误报警告，要求 README 文件出现在镜像目录结构 `{category}/{image}/{version}/{os-version}/` 下，但 PR #2790 仅更新了根目录的 README 文档，属于合法变更。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确判定为 infra-error（置信度: 高），根因是 CI pipeline 脚本缺少对根目录文档文件的豁免逻辑。该修复需要由 CI 流水线团队在 `eulerpublisher` 工具侧实施，本仓库无需任何代码改动。PR 变更内容（README 文档中 Tags 表格更新）本身无质量问题。

## 潜在风险
无