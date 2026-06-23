# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式（关联 模式11：YAML / 元数据文件错误）
- 新模式标题: image-list条目值格式不符
- 新模式症状关键词: `Missing required image root directory`, `parse_image_prefix`, `image-list.yml`, `multi-scene processing`

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
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/format.py:156`（`parse_image_prefix` 函数）
- 失败原因: `Database/image-list.yml` 中新增的 `percona: percona` 条目的值格式不满足 CI 工具 `parse_image_prefix` 的期望——函数处理变更文件 `Database/percona/README.md` 时，无法根据该条目解析出有效的镜像根目录。

### 与 PR 变更的关联

PR 在 `Database/image-list.yml` 中新增了 `percona: percona` 条目。CI 工具 `eulerpublisher` 的 `format.py:parse_image_prefix` 函数遍历变更文件列表，对每个文件查表获取镜像根目录。当处理到 `Database/percona/README.md` 时，函数在 `Database/image-list.yml` 中查找 `percona` 条目，但其值 `percona`（仅镜像目录名）未能通过函数的路径匹配逻辑，引发 ValueError。

根据项目 README 中对 `image-list.yml` 的格式说明，值应包含完整的场景前缀和尾部斜杠（如 `AI/OPEA/AudioQnA/Image_1/`），而当前使用的是简短形式。现有旧条目（`tidb: tidb`、`milvus: milvus` 等）也使用简短形式但未触发此错误，推测 CI 工具近期更新了对新条目值的格式校验，要求使用带场景前缀的完整相对路径。

## 修复方向

### 方向 1（置信度: 中）
将 `Database/image-list.yml` 中 `percona: percona` 的值从简短形式改为带场景前缀和尾部斜杠的完整相对路径格式：

- 修改为 `percona: Database/percona/`
- （若 CI 工具只接受相对于当前场景目录的路径）修改为 `percona: percona/`（仅补充尾部斜杠）

同时检查项目中所有 `image-list.yml` 的格式一致性，确保新条目的值格式与 CI 工具 `parse_image_prefix` 的路径构造/匹配逻辑兼容。

### 方向 2（置信度: 低）
若方向 1 无效，可能是 CI 工具在加载 `Database/image-list.yml` 时未正确读取 PR 分支的文件内容（例如使用了 master 分支的缓存版本）。此时需排查 CI 工具的文件加载逻辑，确认其读取的是已克隆的 PR 分支仓库文件。

## 需要进一步确认的点
1. **`eulerpublisher/update/container/app/format.py:parse_image_prefix` 的实际实现**——需要阅读源码确认该函数：
   - 如何从 `Database/image-list.yml` 中加载条目
   - 如何用条目值与文件路径做匹配（前缀匹配？字符串包含？）
   - 对值的格式有何期望（是否需要场景前缀、尾部斜杠等）
2. **CI 工具加载 image-list.yml 的来源**——确认 `format.py` 是从已克隆的 PR 分支仓库读取，还是从 CI 环境中的其他路径读取，排除缓存/路径问题
3. **现有简短格式条目的兼容性**——确认 `tidb: tidb`、`milvus: milvus` 等现有条目在 CI 同一流程中是否也被处理、是否正常通过，以确定是新格式要求还是仅影响特定文件路径

## 修复验证要求
1. code-fixer 必须在修改 `Database/image-list.yml` 后，检查 `eulerpublisher` 工具中 `parse_image_prefix` 的实际源码，确认新值格式与函数的路径解析逻辑一致
2. 验证修改后 `Database/percona/README.md`（以及变更列表中其他 `Database/percona/` 目录下的文件）均能通过 `parse_image_prefix` 的路径匹配
3. 若修改了 `image-list.yml` 的条目值格式，需检查同文件中其他现有条目是否需要同步更新格式以保持一致性
