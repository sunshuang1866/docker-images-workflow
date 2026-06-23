# 修复摘要

## 修复的问题
`Database/image-list.yml` 中 `percona` 条目值格式不符合 CI 工具 `parse_image_prefix` 的路径解析要求，导致 `ValueError: Missing required image root directory for multi-scene processing`。

## 修改的文件
- `Database/image-list.yml`: 添加 `percona: Database/percona/` 条目，使用带场景前缀和尾部斜杠的完整相对路径格式（符合 README 中 `image-list.yml` 格式规范）。

## 修复逻辑
CI 工具 `eulerpublisher` 的 `format.py:parse_image_prefix` 函数在处理变更文件 `Database/percona/README.md` 时，在 `Database/image-list.yml` 中查找 `percona` 条目用于解析镜像根目录。原始 PR 添加了 `percona: percona`（简短形式），但 CI 工具更新后要求条目值使用完整场景路径格式（如 README 规范的 `Database/percona/`），简短形式无法通过路径匹配逻辑，触发 ValueError。修复使用 `percona: Database/percona/` 替代简短形式，符合 README 中 `image-list.yml` 的规范格式（`SceneDir/ImageDir/`），使 `parse_image_prefix` 能正确解析镜像根目录。

## 潜在风险
- `Database/image-list.yml` 中其他旧条目（如 `tidb: tidb`、`milvus: milvus` 等）仍使用简短格式。根据 CI 分析报告，这些旧条目在 CI 流程中未触发错误（可能是 CI 工具对已存在条目有兼容处理）。未来 CI 工具若统一校验所有条目格式，可能需要同步更新。
- 若 CI 工具的路径构造逻辑与预期有差异（如 `value + filename` vs `value/ + filename`），可能仍需进一步调整。但当前修改严格遵循 README 规范的格式，是最合理的选择。