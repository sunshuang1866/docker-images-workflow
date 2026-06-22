# 修复摘要

## 修复的问题
`Database/image-list.yml` 缺少 `percona` 条目，导致 CI 预检工具 `parse_image_prefix` 无法将 `Database/percona/README.md` 等根层级文件关联到 percona 镜像目录。

## 修改的文件
- `Database/image-list.yml`: 新增 `percona: percona` 条目，与仓库中其他 18 个 Database 镜像保持一致的注册格式。

## 修复逻辑
CI 工具 `eulerpublisher` 的 `parse_image_prefix` 函数通过 `image-list.yml` 建立镜像名到根目录的映射。percona 镜像的文件结构（README.md、meta.yml、doc/ 在根层级，Dockerfile 在版本子目录）与所有已有镜像完全一致，但因 `image-list.yml` 中缺少 `percona` 条目，导致 CI 校验 `Database/percona/README.md` 时抛出 `ValueError: Missing required image root directory`。修复方式为在 `image-list.yml` 末尾追加 `percona: percona`，格式与已有条目（如 `tidb: tidb`、`neo4j: neo4j`）完全一致。

注意：`Database/image-list.yml` 不在原始 PR 的 `changed_files` 列表中，但 CI 错误消息明确指示 `Required action: Specify the image root directory in Database/image-list.yml`，且该文件是新增镜像时必须同步更新的项目注册表。

## 潜在风险
无。修改仅追加一行，格式与已有条目一致，不影响任何已有镜像的 CI 校验。