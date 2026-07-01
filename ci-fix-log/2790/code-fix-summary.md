# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施误判（infra-error），根因在于 `eulerpublisher/update/container/app/update.py` 中的 appstore 预检脚本未排除根目录文档文件，导致纯文档类 PR 被路径校验拦截。

## 修改的文件
- 无需修改（`README.en.md` 和 `README.md` 的内容变更本身正确无误）

## 修复逻辑
分析报告明确指出：这是 CI appstore 预检工具 `update.py` 的校验范围误判 —— 该工具设计目标是校验 `{image-version}/{os-version}/Dockerfile` 等镜像目录结构的合规性，但当前未排除仓库根目录的文档文件（如 `README.md`、`README.en.md`），导致纯文档 PR 被拦截。实际修复应在 `update.py` 中增加根级文档文件的过滤逻辑，但该文件不在本 PR 的变更文件列表中，且任务约束禁止修改 `pr.changed_files` 之外的文件。PR 的 README 内容更新本身无任何问题。

## 潜在风险
无。PR 仅更新了 README 中的镜像 Tags 列表，属于纯文档变更，对镜像构建和质量无任何影响。