# CI 失败分析报告

## 基本信息
- PR: #2751 — 【自动升级】openvelinux容器镜像升级至velinux/1.0+velinux2版本.
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 版本路径超层级
- 新模式症状关键词: Failed to check file path, image-version, os-version, format.py, _parse_image_info

## 根因分析

### 直接错误
```
2026-06-25 12:26:39,693-INFO: The image specification check for releasing on appstore has passed.
Traceback (most recent call last):
  File ".../eulerpublisher/update/container/app/update.py", line 367, in <module>
    if obj.check_updates():
  File ".../eulerpublisher/update/container/app/update.py", line 256, in check_updates
    if _check_app_image(file=file) != 0:
  File ".../eulerpublisher/update/container/app/update.py", line 69, in _check_app_image
    name, tag, arch = format.parse_meta_yml(file=file)
  File ".../eulerpublisher/update/container/app/format.py", line 53, in parse_meta_yml
    os_version, image_version = _parse_image_info(file=file, prefix=prefix)
  File ".../eulerpublisher/update/container/app/format.py", line 101, in _parse_image_info
    raise Exception(
Exception: Failed to check file path: Cloud/openvelinux/velinux/1.0 velinux2/24.03-lts-sp3/Dockerfile, the correct `Dockerfile` or `Distrofile` path should be {image-version}/{os-version}/Dockerfile or {image-version}/{os-version}/Distrofile
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:101`（`_parse_image_info` 函数）
- 失败原因: 新增 Dockerfile 路径为 `Cloud/openvelinux/velinux/1.0 velinux2/24.03-lts-sp3/Dockerfile`，相对于镜像根目录（`Cloud/openvelinux/`）包含三个目录层级（`velinux/`, `1.0 velinux2/`, `24.03-lts-sp3/`），但 CI 校验工具 `format.py` 期望严格的两级结构 `{image-version}/{os-version}/Dockerfile`，路径解析失败。

### 与 PR 变更的关联
**直接关联**。PR 新增了 `velinux/1.0+velinux2` 版本镜像。该版本标识 `velinux/1.0+velinux2` 本身包含 `/` 字符，映射到文件系统时形成三层目录结构，破坏了仓库要求的 `{image-version}/{os-version}` 两级路径规范。此外，meta.yml 中记录的 path 为 `velinux/1.0+velinux2/24.03-lts-sp3/Dockerfile`（`+` 分隔），但实际文件系统路径为 `velinux/1.0 velinux2/24.03-lts-sp3/Dockerfile`（空格分隔），两者不一致。

## 修复方向

### 方向 1（置信度: 高）
将 `velinux/1.0+velinux2` 版本对应的目录路径扁平化，使相对于镜像根目录的路径严格保持 `{image-version}/{os-version}` 两级：例如将版本号中的 `/` 替换为 `-` 或 `_`，使目录变为 `velinux-1.0+velinux2/24.03-lts-sp3/Dockerfile`，同时同步更新 meta.yml 的 path 字段和 image-info.yml、README.md 中的引用链接。

### 方向 2（置信度: 中）
如果 `velinux/` 前缀是镜像的子分类标识（类似 `OPEA/AudioQnA/` 的多级方案目录结构），则需要确认 openvelinux 的 `image-list.yml` 是否已配置对应的最小目录单元路径，以及 CI 校验逻辑是否支持超过两级的目录层级（即 `format.py` 中的 `_parse_image_info` 需要适配三级路径）。否则需按方向 1 扁平化处理。

## 需要进一步确认的点
1. meta.yml 中 path 字段使用 `+`（`velinux/1.0+velinux2`），但实际目录名使用空格（`1.0 velinux2`），需确认这是 git diff 的展示问题还是真实的路径不一致。
2. 仓库中是否已有其他多级版本的先例（如 `Bigdata/` 或 `AI/OPEA/` 下的解决方案级目录），这些路径是否也遵循 `{image-version}/{os-version}` 规范，还是允许额外层级。
3. `format.py` 中 `_parse_image_info` 函数的完整实现，确认其对多级路径的容忍能力。

## 修复验证要求
1. 确认 openvelinux 镜像的 `image-list.yml`（`Cloud/openvelinux/image-list.yml` 或 `Cloud/image-list.yml`）中是否已注册新版本条目，如有缺失需补充。
2. 修复目录路径后，在本地模拟 CI `format.py` 的路径解析逻辑（从 meta.yml 的 path 字段推导 image-version 和 os-version），确保能正确解析。
3. 验证 README.md 和 image-info.yml 中指向新 Dockerfile 的链接与修复后的实际路径一致。
