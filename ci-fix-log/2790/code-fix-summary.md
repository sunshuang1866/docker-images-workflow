# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error）：appstore 发布规范预检对所有 PR 无差别执行路径校验，纯文档 PR（仅修改根目录 `README.md`、`README.en.md`）被误报失败。PR 变更文件本身无任何代码缺陷，无需修改。

## 修改的文件
无（无需对 `README.en.md` 和 `README.md` 做任何修改）

## 修复逻辑
该失败属于 CI 基础设施配置问题，根因在 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑未区分"应用镜像 PR"和"纯文档 PR"。PR 修改的两个 README 文件位于仓库根目录，不在 appstore 要求的 `{Category}/{AppName}/...` 子目录结构中，因此被校验工具误报为路径错误。实际上这两个文件是仓库级别的文档，内容完全正确，不存在需要修复的代码问题。

正确的修复方向是修改 CI 流水线或 `update.py`，对仅包含根目录文档变更的 PR 跳过 appstore 发布规范预检步骤。但 `update.py` 不在本 PR 的 `pr.changed_files` 范围内，因此本次不做代码修改。

## 潜在风险
无。不涉及任何代码变更。