# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-23 04:18:09,985-.../update.py[line:222]-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
Traceback (most recent call last):
  File ".../update/container/app/update.py", line 365, in <module>
    if obj.check_code():
  File ".../update/container/app/update.py", line 270, in check_code
    head, body, fail_count = format.check_report(self.change_files)
  File ".../update/container/app/format.py", line 188, in check_report
    _, prefix = parse_image_prefix(change_file)
  File ".../update/container/app/format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in Database/image-list.yml.
File: Database/percona/README.md
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/.../format.py:156`（`parse_image_prefix` 函数）
- 失败原因: CI 格式校验脚本的 `parse_image_prefix` 函数在处理 `Database/percona/README.md` 时，无法从 `Database/image-list.yml` 中解析出对应的镜像根目录（image root directory），抛出 ValueError。

### 与 PR 变更的关联

**PR 直接触发了此失败**。PR 在 `Database/percona/` 目录下新增了 8 个文件，同时向 `Database/image-list.yml` 添加了 `percona: percona` 条目。CI 的差异检测识别出这 8 个新增文件，并在 `check_report` 中逐一校验。

关键观察：CI 对前 4 个 Dockerfile/配置类文件（位于 `Database/percona/8.4.8/24.03-lts-sp3/` 版本子目录下）校验通过，但在处理第 5 个文件 `Database/percona/README.md`（位于镜像根目录层级，不在版本子目录内）时失败。这说明 `parse_image_prefix` 对**版本子目录下的 Dockerfile** 和**镜像根目录下的非 Dockerfile 文件**采用了不同的解析逻辑：

- 对版本子目录下的文件（如 `.../percona/8.4.8/24.03-lts-sp3/Dockerfile`），函数可能直接从路径结构中提取镜像名。
- 对镜像根目录下的文件（如 `.../percona/README.md`），函数依赖 `image-list.yml` 条目进行匹配，而当前条目 `percona: percona` 的值 `percona` 在匹配 `Database/percona/README.md` 时可能因不包含场景前缀（`Database/`）而匹配失败。

## 修复方向

### 方向 1（置信度: 中）
`Database/image-list.yml` 中 `percona: percona` 条目的值部分可能需要包含完整场景路径或遵循特定格式（如带尾斜杠 `percona/` 或完整路径 `Database/percona/`），以使 `parse_image_prefix` 能正确匹配镜像根目录层级的文件。检查同仓库中其他已有 README.md 在镜像根目录的场景（如有可能），对比其 `image-list.yml` 条目格式，将 percona 条目修正为一致格式。

### 方向 2（置信度: 低）
若条目格式已正确，则可能是 CI 工具 `eulerpublisher` 中 `format.py` 的 `parse_image_prefix` 函数对镜像根目录层级文件的处理存在缺陷。此情况需要向 CI 工具维护者报告，而非修改 PR。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/format.py` 中 `parse_image_prefix` 函数的完整实现逻辑，特别是它如何区分 Dockerfile 路径和根目录文件路径、如何利用 `image-list.yml` 构建匹配前缀。
- 仓库中其他场景（如 AI/、Bigdata/ 等）的 `image-list.yml` 中，是否存在带根目录级 README.md/metadata 文件的镜像条目，其格式与 `percona: percona` 有何异同。
- PR #2703（`fix/2698` 分支）与 PR #2698 原始分支的关系：当前日志来自 `fix/2698` 的 #2703 号 PR 构建，需确认原 PR #2698 的 `image-list.yml` 修改是否一致，以及是否为修复尝试。

## 修复验证要求
- code-fixer 在提交前，必须对比仓库中其他已通过 CI 校验的、带有根目录级别 README.md 的镜像，确认其 `image-list.yml` 中对应条目的值格式，确保 percona 条目与这些条目格式一致。
- 验证修改后 `parse_image_prefix` 能正确解析 `Database/percona/README.md` 以及 `Database/percona/doc/image-info.yml`、`Database/percona/meta.yml` 等根目录文件。
