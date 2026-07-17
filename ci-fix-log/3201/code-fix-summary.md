# 修复摘要

## 修复的问题
PR #3201 在 `AI/maca-sdk/` 下新增镜像但未同步更新 `AI/image-list.yml`，导致 CI 预检工具 `format.py` 的 `parse_image_prefix` 函数无法为 `AI/maca-sdk/README.md` 解析出镜像根目录，抛出 `ValueError`。

## 修改的文件
- `AI/image-list.yml`: 新增 `maca-sdk: maca-sdk` 条目，位于 `llvm-build-deps` 与 `mindspore` 之间，保持字母序排列

## 修复逻辑
根据项目 README 规范，每个场景目录下必须包含 `image-list.yml`，新增镜像时需同步补充对应条目。`format.py` 通过 `image-list.yml` 查找镜像根目录以便校验 `meta.yml` 和 `README.md`。本次修复在 `AI/image-list.yml` 中添加 `maca-sdk: maca-sdk`，key 与目录名一致，值指向镜像根目录 `maca-sdk/`（相对于 `AI/`），格式与其他同类条目（如 `cuda: cuda`、`mindspore: mindspore`）保持一致。

## 潜在风险
无