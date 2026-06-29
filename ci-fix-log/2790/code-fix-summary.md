# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`：appstore 发布规范预检工具对纯文档 PR 强制执行镜像路径校验，导致 `README.en.md` 和 `README.md` 被误判为 "Path Error"。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定为基础设施错误（infra-error），与 PR 变更内容无关。PR 仅更新了两份根目录 README 文档中的基础镜像 Supported Tags 表格，变更本身不存在语法或逻辑错误。CI 的 `update.py` 预检工具不应对纯文档 PR 执行镜像目录路径校验，这是 CI 流水线层面需要调整的问题，不涉及源代码修改。

## 潜在风险
无