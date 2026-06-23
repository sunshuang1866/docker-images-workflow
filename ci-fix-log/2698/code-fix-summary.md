# 修复摘要

## 修复的问题
在 `Database/image-list.yml` 中注册 `percona` 镜像的根目录（`percona: percona`），解决 CI 预检工具 `parse_image_prefix()` 无法确定 `Database/percona/README.md` 等文件所属镜像根目录的问题。

## 修改的文件
- `Database/image-list.yml`: 新增 `percona: percona` 条目（第 19 行），将 percona 镜像根目录注册为 `Database/percona/`

## 修复逻辑
CI 失败的直接原因是 `format.parse_image_prefix()` 遍历 PR 变更文件列表时，对 `Database/percona/README.md` 等文件无法在 `Database/image-list.yml` 中找到对应的镜像根目录，抛出 ValueError。根因是 `Database/image-list.yml` 中缺少 `percona` 条目。原始 PR（`pr-head` 分支）的 git diff 确认包含此变更（`git diff master..pr-head -- Database/image-list.yml` 显示新增 `+  percona: percona`），但当前 fix 分支（基于 master）未包含该变更。添加此条目后，所有 `Database/percona/` 下的文件均能正确映射到已注册的镜像根目录，CI 预检将不再报错。

## 潜在风险
无。此修改与原始 PR 的变更完全一致，且与 `Database/image-list.yml` 中其他镜像条目（如 `mysql`、`redis` 等）格式相同。