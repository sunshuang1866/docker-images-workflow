# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 多场景镜像根目录解析失败
- 新模式症状关键词: Missing required image root directory, multi-scene processing, parse_image_prefix, image-list.yml

## 根因分析

### 直接错误
```
Traceback (most recent call last):
  File ".../eulerpublisher/update/container/app/update.py", line 365, in <module>
    if obj.check_code():
  File ".../update/container/app/update.py", line 270, in check_code
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
- 失败位置: `eulerpublisher/update/container/app/format.py:156`（`parse_image_prefix` 函数）
- 失败原因: CI 预检工具在处理 `Database/percona/README.md` 时，无法从 `Database/image-list.yml` 中解析出该文件对应的镜像根目录，触发 `ValueError`。PR 已向 `image-list.yml` 追加 `percona: percona` 条目（格式与同文件中其他条目 `tidb: tidb`、`milvus: milvus` 等一致），但 `parse_image_prefix` 仍判定根目录缺失。

### 与 PR 变更的关联
PR 新增了 percona 镜像的全部文件（Dockerfile、entrypoint.sh、config、meta.yml、README.md、image-info.yml），并修改 `Database/image-list.yml` 添加 `percona: percona`。CI 失败直接由这些新增文件触发——`format.check_report()` 遍历变更文件列表，在解析 `Database/percona/README.md` 的镜像前缀时失败。entry 的格式与其他条目一致，但 CI 校验逻辑未能正确识别新条目。

## 修复方向

### 方向 1（置信度: 中）
检查 `parse_image_prefix` 的具体实现逻辑，确认其对 `image-list.yml` 条目的期望格式。可能的原因包括：

**(a)** 函数要求条目值为镜像最小目录单元的**完整相对路径**（如 `percona/8.4.8/24.03-lts-sp3` 而非仅 `percona`），或要求包含场景前缀（如 `Database/percona`）。需对照同仓库其他正常工作的场景（如 tidb、milvus）的 `image-list.yml` 条目与实际目录结构，确认其映射关系。

**(b)** 函数在解析到 `percona` 条目后，可能进一步校验该根目录下是否存在必需文件（如 `meta.yml` 或 `Dockerfile`），而 README.md 位于 `Database/percona/` 层级而非版本子目录下，导致校验失败。

### 方向 2（置信度: 低）
`image-list.yml` 文件中最后一行 `percona: percona` 缺少结尾换行符（diff 中显示 `\ No newline at end of file`），可能导致部分 YAML 解析器或后续字符串匹配逻辑异常。可验证在条目末尾添加换行符是否能消除该错误。

## 需要进一步确认的点
1. **查看 `format.py` 源码**：需要获取 `eulerpublisher/update/container/app/format.py` 中 `parse_image_prefix` 函数（第 156 行附近）和 `check_report` 函数（第 188 行附近）的完整实现，以理解其从 `image-list.yml` 解析镜像根目录的具体逻辑。
2. **参照已成功通过的镜像**：查看 `Database/tidb` 或 `Database/milvus` 的完整目录结构（特别是 README.md、meta.yml 的位置层级）和对应的 `image-list.yml` 条目格式，作为 percona 条目格式的参考模板。
3. **确认 README.md 的正确位置**：根据项目最小目录单元规范，确认 README.md 应放置在 `Database/percona/`（镜像级）还是 `Database/percona/8.4.8/24.03-lts-sp3/`（版本级）下。

## 修复验证要求
- code-fixer 必须首先获取 `eulerpublisher/update/container/app/format.py` 中 `parse_image_prefix` 和 `check_report` 的完整源码，理解其镜像根目录解析逻辑后再修改。
- code-fixer 必须参照一个与 percona 目录结构相同且已通过 CI 的同仓库镜像案例（如 `Database/tidb`），确认 `image-list.yml` 条目格式、meta.yml 路径层级、README.md 位置三者的对应关系，确保修改方式与该成功案例一致。
