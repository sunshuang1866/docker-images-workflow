# 修复摘要

## 修复的问题
PR #3201 新增 maca-sdk 镜像时遗漏在 `AI/image-list.yml` 中注册该镜像的根目录条目，导致 CI 元数据完整性校验（`parse_image_prefix`）失败。

## 修改的文件
- `AI/image-list.yml`: 在 `images` 列表末尾添加 `maca-sdk: maca-sdk` 条目，将 `AI/maca-sdk/` 注册为 maca-sdk 镜像的根目录路径。

## 修复逻辑
CI 预检工具 `format.py` 的 `parse_image_prefix` 函数在遍历变更文件时，通过 `image-list.yml` 查找每个文件对应的镜像根目录。PR 在 `AI/` 场景下新增了 maca-sdk 镜像的四个文件（Dockerfile、EUR.repo、README.md、meta.yml），但未在 `AI/image-list.yml` 中添加 `maca-sdk` 条目，导致 `parse_image_prefix` 抛出 `ValueError("Missing required image root directory for multi-scene processing.")`。添加该条目后，CI 工具即可正确解析 `AI/maca-sdk/README.md` 的归属。

## 潜在风险
无。该修改仅追加一行 YAML 条目，不影响现有镜像的解析逻辑。