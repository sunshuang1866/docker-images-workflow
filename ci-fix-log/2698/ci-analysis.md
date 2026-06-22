# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: image-list条目与文件路径不匹配
- 新模式症状关键词: Missing required image root directory, multi-scene processing, parse_image_prefix, image-list.yml, README.md

## 根因分析

### 直接错误
```
Traceback (most recent call last):
  File "/…/eulerpublisher/update/container/app/format.py", line 188, in check_report
    head, body, fail_count = format.check_report(self.change_files)
  File "/…/eulerpublisher/update/container/app/format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in Database/image-list.yml.
File: Database/percona/README.md
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156`（`parse_image_prefix` 函数）
- 失败原因: CI 预检工具在处理 `Database/percona/README.md` 时，无法根据 `Database/image-list.yml` 中 `percona: percona` 条目将该文件关联到 percona 镜像的根目录。该文件位于镜像根层级（`Database/percona/`），而非版本号子目录（`Database/percona/8.4.8/24.03-lts-sp3/`）内。`parse_image_prefix` 函数可能仅能匹配位于 Dockerfile 所在版本目录内的文件（即通过 `meta.yml` 中的 `path` 字段反查），导致根层级文件无法通过校验。

### 与 PR 变更的关联
PR 新增了 percona 镜像的完整目录结构，包括：
- 版本目录内文件（Dockerfile、config、entrypoint.sh）—— 这些通过了校验
- 根层级文件（README.md、doc/image-info.yml、meta.yml、doc/picture/logo.png）—— `README.md` 触发了校验失败

问题直接由 PR 的文件结构布局引起：将 README.md、doc/、meta.yml 放在 `Database/percona/` 根层级，而非版本子目录内，与 CI 工具的预期不符。

## 修复方向

### 方向 1（置信度: 中）
将 `README.md`、`doc/`、`meta.yml` 从 `Database/percona/` 根层级移入版本子目录 `Database/percona/8.4.8/24.03-lts-sp3/` 内，使所有非 image-list 变更文件均位于 Dockerfile 所在目录下，与 CI 预检工具的 `parse_image_prefix` 匹配逻辑一致。同时检查 `meta.yml` 中 `path` 字段是否需要同步调整。

### 方向 2（置信度: 低）
不移动文件，改为检查 `Database/image-list.yml` 中 `percona` 条目的值格式是否需要调整为包含完整相对路径（如 `percona/8.4.8/24.03-lts-sp3`）或包含场景前缀（如 `Database/percona`）。但对比同文件中其他条目（如 `tidb: tidb`）的格式，此方向可能性较低。

## 需要进一步确认的点
1. `eulerpublisher` 工具中 `parse_image_prefix` 的具体实现逻辑：它是通过 `image-list.yml` 的 value 做路径前缀匹配，还是通过读取 `meta.yml` 中 Dockerfile 路径反推
2. 仓库中其他已有镜像（如 tidb、neo4j）的 README.md 和 doc/ 文件是放在镜像根层级还是版本子目录内——这能确定 CI 工具的实际预期布局
3. 如果文件结构必须调整，需确认 `meta.yml`、`doc/image-info.yml` 的引用路径是否会受影响
