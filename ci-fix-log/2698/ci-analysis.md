# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI预检读取目标分支元数据
- 新模式症状关键词: parse_image_prefix, Missing required image root directory, multi-scene processing, image-list.yml, pre-merge validation

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
Required action: Specify the image root directory in Database/image-list.yml.
File: Database/percona/README.md
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156` (`parse_image_prefix` 函数)
- 失败原因: CI 预检工具 `parse_image_prefix` 在处理文件 `Database/percona/README.md` 时，无法从 `Database/image-list.yml` 中找到 `percona` 镜像的根目录映射，抛出 ValueError。该 PR 已正确添加 `percona: percona` 到 `Database/image-list.yml`，但 CI 预检阶段可能读取的是 workspace（upstream master 分支）中的 `image-list.yml`，而非 PR 分支中已更新的版本。

### 与 PR 变更的关联

**PR 直接相关，但非 PR 变更错误所致。** 具体逻辑：

1. PR 在 `Database/image-list.yml` 中新增了 `percona: percona` 条目，格式与现有条目（`tidb: tidb`、`neo4j: neo4j` 等）完全一致，变更本身正确。
2. `parse_image_prefix` 对于位于版本/架构子目录下的文件（如 `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`）可以通过目录结构推断出镜像根目录，无需依赖 `image-list.yml`，因此能成功处理。
3. 对于位于镜像根级别的文件（如 `Database/percona/README.md`、`Database/percona/meta.yml`），该函数无法从路径推断镜像根目录，必须依赖 `image-list.yml` 进行查找。
4. CI 工作流在 workspace (`/home/jenkins/.../x86-64/openeuler-docker-images`) 中运行 `eulerpublisher` 工具并从该 workspace 读取 `Database/image-list.yml`，而 workspace 中的代码为 upstream master 分支（未合并此 PR），其中不包含 `percona` 条目，导致查找失败。

这形成了鸡生蛋问题：PR 要添加的镜像条目正是本次 PR 在 `image-list.yml` 中新增的内容，但 CI 预检阶段读取的是目标分支（master）的旧版 `image-list.yml`。

## 修复方向

### 方向 1（置信度: 中）
**这是 CI 基础设施问题，无需修改 PR 代码。** 需要 CI 维护者调整 `eulerpublisher` 工具的行为：在 `parse_image_prefix` 中，应从 PR 的克隆仓库（`/tmp/eulerpublisher_*/ci/container/check/...`）读取 `image-list.yml`，而非从 Jenkins workspace。或者，在 `format.py` 中将 `parse_image_prefix` 对根级文件（非版本子目录下的文件）的校验放宽为警告而非硬错误。

### 方向 2（置信度: 低）
如果 CI 工具确实从 PR 克隆仓库读取 `image-list.yml` 但仍失败，可能是 `image-list.yml` 文件末尾缺少换行符（git diff 中显示 `\ No newline at end of file`）导致 YAML 解析器未能读取最后一行 `percona: percona`。但此问题在 PR 修改前已存在（`milvus: milvus` 同样无尾随换行），且其他镜像均正常工作，因此该方向可能性较低。

## 需要进一步确认的点

1. **`parse_image_prefix` 的 `image-list.yml` 读取路径**：需确认 `eulerpublisher/update/container/app/format.py:156` 是从哪个路径读取 `Database/image-list.yml`——是 Jenkins workspace（upstream master）还是 PR 克隆目录（`/tmp/eulerpublisher_*/`）。这是确定根因的关键。
2. **其他新镜像 PR 是否遇到同类问题**：检索近期其他新增镜像的 CI 记录，确认此问题是否为通用问题还是一例特殊情况。
3. **`image-list.yml` 的尾随换行符是否影响解析**：虽然已有镜像（`milvus`）在无尾随换行符情况下未出问题，但值得在 PR 克隆仓库中验证 YAML 解析是否确实加载了 `percona: percona` 条目。

## 修复验证要求

无需代码修复验证。此为 CI 基础设施问题，需 CI 维护者确认 `eulerpublisher` 工具读取 `image-list.yml` 的来源路径，或确认该 PR 可通过管理员权限 bypass 预检后合并。
