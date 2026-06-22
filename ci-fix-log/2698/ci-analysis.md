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
2026-06-23 00:20:27,152-.../update.py[line:356]-INFO: Difference: [
    "Cloud/image-list.yml",
    "Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile",
    "Cloud/percona/8.4.8/24.03-lts-sp3/config/conf.d/my.cnf",
    "Cloud/percona/8.4.8/24.03-lts-sp3/config/my.cnf",
    "Cloud/percona/8.4.8/24.03-lts-sp3/entrypoint.sh",
    "Cloud/percona/README.md",
    "Cloud/percona/doc/image-info.yml",
    "Cloud/percona/doc/picture/logo.png",
    "Cloud/percona/meta.yml",
    "Database/percona/8.4.8/24.03-lts-sp3/Dockerfile",
    "Database/percona/8.4.8/24.03-lts-sp3/config/conf.d/my.cnf",
    "Database/percona/8.4.8/24.03-lts-sp3/config/my.cnf",
    "Database/percona/8.4.8/24.03-lts-sp3/entrypoint.sh",
    "Database/percona/README.md",
    "Database/percona/doc/image-info.yml",
    "Database/percona/doc/picture/logo.png",
    "Database/percona/meta.yml"
]
...
Traceback (most recent call last):
  File ".../update.py", line 365, in <module>
    if obj.check_code():
  File ".../update.py", line 270, in check_code
    head, body, fail_count = format.check_report(self.change_files)
  File ".../format.py", line 188, in check_report
    _, prefix = parse_image_prefix(change_file)
  File ".../format.py", line 156, in parse_image_prefix
    raise ValueError(
ValueError: Missing required image root directory for multi-scene processing.
Required action: Specify the image root directory in Database/image-list.yml.
File: Database/percona/README.md
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156`（`parse_image_prefix` 函数）
- 失败原因: CI `check_code` 流程检测到本次变更同时涉及 `Cloud/` 和 `Database/` 两个场景目录（多场景处理模式），在对变更文件逐一校验时，`parse_image_prefix` 无法在 `Database/image-list.yml` 中找到 `Database/percona/README.md` 所对应的镜像根目录条目。

### 与 PR 变更的关联

**PR diff 中已包含修复**: PR diff 明确在 `Database/image-list.yml` 中添加了 `percona: percona` 条目。然而 CI 日志仍然报"Missing required image root directory in Database/image-list.yml"，存在矛盾。

可能原因分析（按可能性排序）：

1. **Cloud 侧 percona 文件缺少注册（最可能，置信度: 中）**：CI Difference 列表中包含 8 个 `Cloud/percona/…` 文件，但这些文件**不在本 PR (#2698) 的 diff 中**。它们来自触发 CI 的上层 PR (#2703: `sunshuang1866:fix/2698 -> master`)。`Cloud/image-list.yml` 中未添加 percona 条目，导致多场景校验模式下报错。错误信息指向 Database 文件可能是因为 `parse_image_prefix` 遍历文件列表时，Database 文件触发了第一个失败（或因函数内部对多场景的特殊处理逻辑）。

2. **CI 克隆的代码版本与 PR diff 不一致（可能性: 中）**：CI 执行 `Clone https://gitcode.com/sunshuang1866/****-docker-images.git` 从 fork 仓库克隆，克隆的 `fix/2698` 分支状态可能与本 PR 的 diff 基线不同步，导致 `Database/image-list.yml` 中实际没有 percona 条目。

3. **image-list.yml 格式问题（可能性: 低）**：PR diff 显示 `Database/image-list.yml` 末尾缺少换行符（`\ No newline at end of file`）。极少数 YAML 解析器对此敏感，可能导致 percona 条目未被正确解析。

## 修复方向

### 方向 1（置信度: 高）
**补充 Cloud/image-list.yml 的 percona 条目**。在 `Cloud/image-list.yml` 中添加 `percona: percona`（类似 Database 侧的修改），使 Cloud 和 Database 两个场景目录的 image-list.yml 均包含 percona 镜像的根目录注册。这是最直接的修复方向，因为 CI 触发了多场景处理模式，要求所有涉及场景的 image-list.yml 都完整注册。

### 方向 2（置信度: 中）
**验证 CI 克隆的分支状态**。确认 `sunshuang1866:fix/2698` 分支上 `Database/image-list.yml` 是否确实包含 `percona: percona` 条目。如果已包含但仍失败，则问题大概率出在 Cloud 侧；如果未包含，则需确认该分支上的 commit 是否与本 PR diff 一致。

## 需要进一步确认的点

1. **确认 Cloud/percona 文件的来源**：PR #2698 的 diff 中不包含任何 `Cloud/percona/` 文件，但 CI 差异列表中出现了 8 个 Cloud percona 文件。需要确认这些文件是否由上游 PR #2703 引入，以及它们是否应该随同本 PR 一起提交。
2. **确认 CI 克隆的实际 branch/commit**：日志显示从 `sunshuang1866/****-docker-images.git` 克隆，需要确认实际 checkout 的 commit hash，排查是否与 PR diff 所指的代码状态一致。
3. **检查 Cloud/image-list.yml 当前内容**：确认是否缺少 percona 条目，因为 Cloud 侧的 percona 文件也需要在对应的 image-list.yml 中注册。
4. **查看 format.py 的 parse_image_prefix 函数实现**：理解多场景处理模式下对 image-list.yml 的具体查找逻辑，确认错误报告的文件名（`Database/percona/README.md`）与实际上缺失条目的场景（可能是 Cloud/）之间的关系。

## 修复验证要求

code-fixer 在修改后必须验证：
1. `Database/image-list.yml` 和 `Cloud/image-list.yml` 均包含 `percona: percona` 条目
2. 两个 image-list.yml 文件均为合法的 YAML 格式
3. 确认 percona 镜像在 Cloud/ 和 Database/ 两个场景目录下的存在方式符合项目规范（避免重复文件，或明确两个场景各自独立的 Dockerfile 路径）
