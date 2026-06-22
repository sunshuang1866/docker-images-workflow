# 修复摘要

## 修复的问题
`Database/image-list.yml` 缺少 `percona: percona` 条目，导致 CI lint 工具 `parse_image_prefix` 在处理 `Database/percona/README.md` 时无法解析出镜像根目录。

## 修改的文件
- `Database/image-list.yml`: 在 `milvus: milvus` 之后添加 `percona: percona` 条目，并补充文件结尾换行符以与其他 image-list.yml 保持一致。

## 修复逻辑
CI 分析报告指出 `format.py:parse_image_prefix()` 在解析变更文件 `Database/percona/README.md` 时，从 `Database/image-list.yml` 中找不到对应的镜像根目录映射。根因是 percona 文件在 fix 分支上被移动到 `Database/percona/` 目录后，`Database/image-list.yml` 漏掉了 `percona: percona` 条目（该条目格式与同文件中 `tidb: tidb`、`milvus: milvus` 等一致）。参照已通过 CI 的 Database 镜像（如 tidb、milvus）的目录结构与 image-list.yml 条目格式，添加缺失条目即可消除 lint 报错。同时补上文件结尾换行符以消除分析报告中方向 2 提到的潜在 YAML 解析异常风险。

## 潜在风险
无。该修改与 `Database/image-list.yml` 中所有现有条目格式一致，仅添加一行映射，不影响现有镜像的 CI 检查。