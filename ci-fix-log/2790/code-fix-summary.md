# 修复摘要

## 修复的问题
CI appstore 发布规范预检对仓库根目录下的纯文档文件（README.md、README.en.md）错误地执行了镜像路径校验，属于 CI 基础设施问题（infra-error），PR 变更的 README 文件本身无代码问题，无需修改。

## 修改的文件
无代码修改。

## 修复逻辑
PR #2790 仅更新了仓库根目录的 README.md 和 README.en.md（更新镜像 Tags 列表和对应链接），属于纯文档维护。CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对所有变更文件执行了镜像路径校验，要求文件必须位于 `Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`、`Base/` 等应用镜像目录下。仓库根目录的 README 文件不属于任何应用镜像目录，因此被误判为路径错误。

根据任务约束，仅允许修改 `pr.changed_files` 列表中的文件（`README.md`、`README.en.md`），而真正需要修复的 CI 校验工具不在可修改范围内。该问题根因是 CI 基础设施校验逻辑过于宽泛，属于 infra-error，无法通过修改 README 文件解决。

## 潜在风险
无。README 文件内容正确，无需任何代码修改。建议由 CI 工具维护者在 `eulerpublisher/update/container/app/update.py` 中对仓库根目录文档文件添加白名单过滤，或通过 PR label 机制跳过纯文档 PR 的 appstore 校验。