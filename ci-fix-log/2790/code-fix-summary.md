# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 `infra-error`（基础设施问题）：appstore 发布规范检查脚本 `eulerpublisher/update/container/app/update.py` 错误地将纯文档 PR（仅修改根目录 `README.md`）纳入镜像发布路径校验范围，导致根目录 `README.md` 被误判为 FAILURE。

## 修改的文件
无。PR 变更的 `README.md` 内容完全正确有效，无需任何修改。

## 修复逻辑
1. 本 PR (#2790) 仅更新了根目录 `README.md` 和 `README.en.md` 中的基础镜像 Tags 列表（添加 24.03-lts-sp3 和 25.09 条目），是一次纯文档更新。
2. CI 失败的直接原因是 `update.py:273` 的 appstore 路径校验逻辑要求变更文件必须符合 `{image}/{version}/{os-version}/Dockerfile` 格式的镜像发布路径，而根目录 `README.md` 不满足此格式，被错误地判定为 FAILURE。
3. 根据分析报告结论："该失败由 PR 变更触发，但 PR 变更内容本身（文档更新）是有效的"。根因在于 CI pipeline 的触发条件和校验逻辑未区分纯文档 PR 与镜像发布 PR。
4. `update.py` 不在 `pr.changed_files` 列表中，无法在此分支中修改。正确的修复方向为：在 CI pipeline 层面增加文件路径过滤，使仅修改仓库根目录 `.md` 文件的 PR 不触发 appstore 检查 job。

## 潜在风险
无。`README.md` 无需修改，不存在代码层面的风险。