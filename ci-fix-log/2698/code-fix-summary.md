# 修复摘要

## 修复的问题
`Database/image-list.yml` 缺少 `percona: percona` 条目，导致 CI 的 `parse_image_prefix` 函数在解析 `Database/percona/README.md` 等镜像根目录文件时抛出 ValueError。

## 修改的文件
- `Database/image-list.yml`: 在 `milvus: milvus` 后追加 `percona: percona` 条目，与同文件中其他镜像条目（如 `cassandra: cassandra`、`mysql: mysql`）格式完全一致。

## 修复逻辑
CI 分析报告定位根因为 `parse_image_prefix` 处理镜像根目录层级文件（如 `Database/percona/README.md`）时，依赖 `Database/image-list.yml` 中的条目来匹配镜像根目录。原始 PR 将 percona 文件从 `Cloud/` 移动到 `Database/`，但 `Database/image-list.yml` 未同步添加 percona 条目（pr-head 分支已有此条目，fix/2698 分支遗漏）。添加 `  percona: percona` 后，`parse_image_prefix` 能正确解析 `Database/percona/README.md`、`Database/percona/doc/image-info.yml`、`Database/percona/meta.yml` 等根目录文件。修改后与 pr-head 分支一致。

## 潜在风险
无。此修改仅追加一行与同文件其他镜像条目格式完全一致的内容，不涉及任何逻辑变更，且与 pr-head 分支验证状态一致。