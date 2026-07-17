# 修复摘要

## 修复的问题
无需代码修改。CI 失败是基础设施问题（infra-error），而非 PR 代码缺陷。

## 修改的文件
无（无需修改任何文件）

## 修复逻辑
CI 失败由 appstore 发布规范预检工具 `update.py` 引起：该工具将 PR 变更中的所有文件都视为候选镜像路径，对根目录下的 `README.md` 进行 `{image-version}/{os-version}/Dockerfile` 格式校验时必然失败。PR #3153 是纯文档更新（在 README.md 中新增基础镜像 Tag 条目），`README.md` 内容本身语法正确、格式合规，不存在任何代码错误。根因在于 CI 预检工具未过滤非镜像目录路径文件（如仓库根目录的 README.md），这是 CI 基础设施/工具的缺陷，需要修改 `update.py` 的文件过滤逻辑，而非修改 PR 中已变更的文件。

由于 `update.py` 不在本次 PR 的 `changed_files` 列表中，且约束规则禁止修改 `changed_files` 之外的任何文件，本修复无需且无法对源代码实施任何变更。

## 潜在风险
无。`README.md` 未被修改，不存在引入新问题的风险。CI 预检工具的问题需由 CI 维护者单独修复。