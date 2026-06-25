# 修复摘要

## 修复的问题
将 `velinux/1.0+velinux2` 版本目录从三级扁平化为二级，使其符合 CI 校验要求的 `{image-version}/{os-version}/Dockerfile` 路径规范。

## 修改的文件
- `Cloud/openvelinux/velinux/1.0 velinux2/24.03-lts-sp3/Dockerfile` → `Cloud/openvelinux/velinux-1.0+velinux2/24.03-lts-sp3/Dockerfile`: 目录重命名（内容不变），三级路径 `velinux/1.0 velinux2/24.03-lts-sp3/` 扁平化为二级 `velinux-1.0+velinux2/24.03-lts-sp3/`
- `Cloud/openvelinux/meta.yml`: path 字段从 `velinux/1.0+velinux2/24.03-lts-sp3/Dockerfile` 改为 `velinux-1.0+velinux2/24.03-lts-sp3/Dockerfile`
- `Cloud/openvelinux/README.md`: Dockerfile 链接 URL 路径同步更新
- `Cloud/openvelinux/doc/image-info.yml`: Dockerfile 链接 URL 路径同步更新

## 修复逻辑
CI `format.py` 的 `_parse_image_info` 函数要求相对于镜像根目录的路径严格为 `{image-version}/{os-version}/Dockerfile` 二级结构。原始 PR 中 `velinux/1.0+velinux2/24.03-lts-sp3/Dockerfile` 有三个目录层级（`velinux/`, `1.0+velinux2/`, `24.03-lts-sp3/`），导致路径解析抛出异常。此外，meta.yml 中使用 `+` 分隔（`1.0+velinux2`）但实际文件系统目录使用空格分隔（`1.0 velinux2`），存在不一致。

修复方案（方向 1）：将嵌套的 `velinux/1.0 velinux2` 目录扁平化为单一目录 `velinux-1.0+velinux2`，使 image-version 解析为 `velinux-1.0+velinux2`，os-version 解析为 `24.03-lts-sp3`，同时消除路径中的空格与 `+` 不一致问题。

## 潜在风险
无。修复仅涉及路径结构调整，Dockerfile 构建内容（`ARG VERSION=velinux/1.0+velinux2`、下载 URL 等）未变，镜像 tag 名称（`velinux/1.0+velinux2-oe2403sp3`）未变，不影响镜像构建和最终产物。