# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
Traceback (most recent call last):
  File ".../eulerpublisher/update/container/app/update.py", line 365, in <module>
    if obj.check_code():
       ^^^^^^^^^^^^^^^^
  File ".../eulerpublisher/update/container/app/update.py", line 270, in check_code
    head, body, fail_count = format.check_report(self.change_files)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../eulerpublisher/update/container/app/format.py", line 188, in check_report
    _, prefix = parse_image_prefix(change_file)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../eulerpublisher/update/container/app/format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in AI/image-list.yml.
File: AI/maca-sdk/README.md
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156`（`parse_image_prefix` 函数）
- 失败原因: PR 在 `AI/` 场景目录下新增了 `maca-sdk` 镜像（含 `Dockerfile`、`EUR.repo`、`README.md`、`meta.yml`），但未在 `AI/image-list.yml` 中注册该镜像的根目录条目。CI 预检工具 `format.py` 在遍历变更文件时，无法从 `image-list.yml` 中找到 `AI/maca-sdk/README.md` 对应的镜像根目录，导致 `parse_image_prefix` 抛出 `ValueError`。

### 与 PR 变更的关联
PR 的变更直接触发了该失败。新增的四个文件（`Dockerfile`、`EUR.repo`、`README.md`、`meta.yml`）均属于新镜像 `maca-sdk`，根据项目规范（见 README 第 2.1 节），每个场景目录下的 `image-list.yml` 必须包含该场景所有镜像的根目录路径。PR 遗漏了对 `AI/image-list.yml` 的修改，导致 CI 元数据完整性校验失败。

## 修复方向

### 方向 1（置信度: 高）
在 `AI/image-list.yml` 的 `images` 列表中添加 `maca-sdk` 条目，将 `AI/maca-sdk/` 注册为 `maca-sdk` 镜像的根目录路径。参考项目中已有的 `AI/image-list.yml` 格式，确保 YAML 语法正确。

## 需要进一步确认的点
- 确认 `AI/image-list.yml` 文件当前的内容格式，以便正确追加条目（需确认是纯 YAML mapping 还是有特殊结构）。
- 确认 README.md 中是否还需要添加 Copyright + SPDX 声明头（见模式17），避免后续 CI 阶段出现次要失败。

## 修复验证要求
（无需对上游源文件做正则 patch，不适用。）
