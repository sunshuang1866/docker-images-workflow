# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: 
- 新模式症状关键词: 

## 根因分析

### 直接错误
```
Traceback (most recent call last):
  File "/.../eulerpublisher/update/container/app/update.py", line 365, in <module>
    if obj.check_code():
  File "/.../eulerpublisher/update/container/app/update.py", line 270, in check_code
    head, body, fail_count = format.check_report(self.change_files)
  File "/.../eulerpublisher/update/container/app/format.py", line 188, in check_report
    _, prefix = parse_image_prefix(change_file)
  File "/.../eulerpublisher/update/container/app/format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in Database/image-list.yml.
File: Database/percona/README.md
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156` (`parse_image_prefix` 函数)
- 失败原因: CI 预检工具检测到本次变更跨多个场景目录（Cloud 和 Database），触发"多场景处理"（multi-scene processing）代码路径。`parse_image_prefix` 在处理 `Database/percona/README.md` 时，在 `Database/image-list.yml` 中找不到对应 percona 的镜像根目录条目（或条目格式不符合多场景处理的要求）。

### 与 PR 变更的关联
PR 在 `Database/` 目录下新增了 percona 镜像的所有文件（Dockerfile、entrypoint.sh、config、README.md、meta.yml、image-info.yml），并在 `Database/image-list.yml` 中追加了 `percona: percona` 条目。但 CI 日志显示变更列表中还包含了 `Cloud/` 目录下的 percona 同类文件（`Cloud/percona/...`），这些 Cloud 目录下的文件**不在本次提供的 PR diff 中**——可能由上游 fix 分支（`fix/2698`, PR #2703）额外携带。这导致 CI 检测到一个镜像同时出现在两个场景目录中，触发了 multi-scene 校验路径，该校验对 `image-list.yml` 条目格式可能有更严格的要求（如需要完整场景路径而非仅镜像名），导致 `parse_image_prefix` 无法正确解析 `percona: percona` 这个条目。

## 修复方向

### 方向 1（置信度: 中）
检查 `fix/2698` 分支上 `Database/image-list.yml` 的实内容，确认 percona 条目格式是否与已有条目（如 `tidb: tidb`）一致。如果一致但仍失败，则 multi-scene 校验路径可能要求 image-list.yml 中的值必须包含场景路径前缀（如 `percona: Database/percona` 或 `percona: Database/percona/`），而非仅镜像名。可在 `eulerpublisher` 仓库中查看 `parse_image_prefix` 的实现确认要求。

### 方向 2（置信度: 低）
排查为何 `fix/2698` 分支携带了 `Cloud/` 目录下的 percona 文件。如果这些 Cloud 文件是无意引入的（如错误合入或重复提交），移除它们可消除 multi-scene 触发条件。如果 Cloud 和 Database 双场景部署是有意设计，则两个场景的 `image-list.yml` 均需正确配置 percona 条目。

## 需要进一步确认的点
1. **`fix/2698` 分支的完整 diff**：当前提供的 PR diff 仅包含 `Database/` 变更，但 CI 日志显示还存在 `Cloud/` 变更。需要获取 `fix/2698` 相对于 master 的完整 diff 确认 Cloud 文件来源。
2. **`parse_image_prefix` 的多场景逻辑**：需要在 `eulerpublisher` 仓库中查看 `format.py:156` 附近代码，确认 multi-scene 校验对 `image-list.yml` 条目的具体格式要求（是否需要全路径、是否需要尾随 `/` 等）。
3. **Cloud 目录的 percona 文件是否预期存在**：确认 Cloud/percona 文件是有意部署还是误提交，决定是移除 Cloud 文件还是补全 Cloud/image-list.yml 条目。

## 修复验证要求
1. 修复后需确认 `check_report` 不再为任何变更文件报 `parse_image_prefix` 的 ValueError。
2. 如果修改涉及 `image-list.yml` 的条目格式，需在所有受影响的场景目录中保持一致。
