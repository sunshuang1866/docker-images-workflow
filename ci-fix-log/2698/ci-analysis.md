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
Traceback (most recent call last):
  File ".../eulerpublisher/update/container/app/update.py", line 365, in <module>
    if obj.check_code():
  File ".../eulerpublisher/update/container/app/update.py", line 270, in check_code
    head, body, fail_count = format.check_report(self.change_files)
  File ".../eulerpublisher/update/container/app/format.py", line 188, in check_report
    _, prefix = parse_image_prefix(change_file)
  File ".../eulerpublisher/update/container/app/format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in Cloud/image-list.yml.
File: Cloud/percona/README.md
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156`
- 失败原因: CI 预检工具（eulerpublisher）在 PR 分支与 master 的差异中检测到了 `Cloud/percona/README.md` 等文件，但在 `Cloud/image-list.yml` 中未找到 `percona` 的镜像根目录条目，导致 `parse_image_prefix` 抛出 `ValueError`。

### 与 PR 变更的关联

PR diff 仅显示向 `Database/percona/...` 添加了镜像文件，并在 `Database/image-list.yml` 中补充了 `percona: percona` 条目。然而 CI 的 `eulerpublisher` 工具在对比 PR 分支与 master 时，额外检测到了 `Cloud/percona/...` 路径下的同名文件（`Dockerfile`、`entrypoint.sh`、README 等共计 8 个）。这些 Cloud 目录下的文件未出现在本次 PR diff 中，但存在于 PR 源分支（`sunshuang1866:fix/2698`）内，导致 CI 预检要求同时在 `Cloud/image-list.yml` 中也声明 `percona` 条目。

**关联判定**：与 PR 间接相关。PR 在 `Database/` 目录下新增了 percona 镜像，但 PR 源分支中残留了 `Cloud/percona/` 下的旧版/误放文件，触发了 `image-list.yml` 完整性校验。

## 修复方向

### 方向 1（置信度: 中）
如果 `Cloud/percona/` 下的文件是误放（镜像应仅在 `Database/` 目录下），则需从 PR 源分支中删除 `Cloud/percona/` 整个目录，确保差异列表中不再出现 Cloud 路径下的 percona 文件。

### 方向 2（置信度: 低）
如果 percona 确实需要同时支持 Cloud 和 Database 两个场景目录，则需在 `Cloud/image-list.yml` 中也追加 `percona: percona`（如模式11所述），与 `Database/image-list.yml` 的改动保持一致。

## 需要进一步确认的点
1. **确认 PR 源分支是否包含 `Cloud/percona/` 目录**：PR diff 未显示该目录，但 CI 差异列表中出现了 8 个 Cloud/percona 文件。需在 PR 源仓库（`sunshuang1866/openeuler-docker-images` 的 `fix/2698` 分支）中检查 `Cloud/percona/` 是否真实存在、是否为误提交的残留文件。
2. **确认 `Cloud/image-list.yml` 当前内容**：需要查看 `Cloud/image-list.yml` 确认是否确实缺少 `percona` 条目。
3. **确认 percona 镜像的预期归属场景**：根据 openEuler 项目规范，percona 属数据库类镜像，应归属 `Database/` 目录。如果 Cloud 目录下的文件无意义，应清除而非补充 image-list.yml。

## 修复验证要求
（无需针对正则 patch 的验证）
