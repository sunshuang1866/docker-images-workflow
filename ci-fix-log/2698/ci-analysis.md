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
2026-06-23 04:18:01,221-.../update.py[line:356]-INFO: Difference: [
    "Database/percona/8.4.8/24.03-lts-sp3/Dockerfile",
    "Database/percona/8.4.8/24.03-lts-sp3/config/conf.d/my.cnf",
    "Database/percona/8.4.8/24.03-lts-sp3/config/my.cnf",
    "Database/percona/8.4.8/24.03-lts-sp3/entrypoint.sh",
    "Database/percona/README.md",
    "Database/percona/doc/image-info.yml",
    "Database/percona/doc/picture/logo.png",
    "Database/percona/meta.yml"
]
Cloning into '/tmp/eulerpublisher_2598wsi1/ci/container/check/****-docker-images'...
...Clone ... successfully.
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
- 失败原因: CI 预检工具 `format.check_report()` 遍历 PR 变更文件列表时，对 `Database/percona/README.md` 调用 `parse_image_prefix()` 无法确定该文件所属的镜像根目录（image root directory），抛出 ValueError。

### 与 PR 变更的关联

PR 变更**应当满足** CI 预检要求：
- PR 在 `Database/image-list.yml` 中新增了 `percona: percona` 条目（第 19 行），将 percona 镜像的根目录注册为 `Database/percona/`
- 文件 `Database/percona/README.md` 的路径完全在已注册的根目录 `Database/percona/` 之下

但 CI 预检工具仍然报告"在 Database/image-list.yml 中未找到该文件的镜像根目录"，这说明存在以下两种可能之一：

1. **CI 工具读取的 image-list.yml 与 PR 提交的不同**：`parse_image_prefix()` 可能从工作区（workspace）而非克隆的 PR 分支中读取 `image-list.yml`，导致读到的是目标分支（master）版本，其中不包含 `percona` 条目。
2. **CI 工具对 README.md 类文件的路径解析逻辑存在局限**：`parse_image_prefix()` 可能只处理版本化子目录下的文件（如 `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`），对直接在镜像根目录下的文件（如 `Database/percona/README.md`）匹配失败。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具 `parse_image_prefix` 从目标分支读取 image-list.yml，而非从 PR 分支读取。** 需要确认 `format.py:parse_image_prefix` 读取 `image-list.yml` 时的文件路径来源。若它从 Jenkins 工作区（master 分支）读取而非从 `/tmp/eulerpublisher_*` 临时克隆目录读取，则需要在 CI 脚本中确保校验阶段使用 PR 分支的 `image-list.yml`。

### 方向 2（置信度: 低）
**`parse_image_prefix` 函数不支持镜像根目录下的通用文件（README.md、meta.yml）。** 如果该函数设计上只处理版本化路径（至少 3-4 层目录深度），则需要对 `Database/percona/README.md` 这类文件做特殊处理（跳过校验或使用更宽松的匹配规则）。

## 需要进一步确认的点

1. `eulerpublisher/update/container/app/format.py` 中 `parse_image_prefix()` 函数的完整实现逻辑：该函数从何处读取 `image-list.yml`（工作区还是克隆目录？），以及路径匹配逻辑如何工作。
2. CI 脚本中 `check_code()` 调用前后的工作目录状态：`format.check_report()` 运行时当前工作目录是工作区还是 `/tmp/eulerpublisher_*` 临时目录。
3. 对比已通过 CI 的类似 PR（如其他数据库镜像首次提交），确认新增镜像的规范流程是否要求 README.md 等文件必须放在特定子目录下。
4. 在 CI 环境中手动验证：将 `Database/percona/README.md` 从 PR 文件变更列表中移除（或改为仅提交版本化子目录下的文件）后，CI 是否能通过——以此确认是否为 README.md 所在路径层级所致。

## 修复验证要求

若修复方向涉及修改 `eulerpublisher` 工具代码，code-fixer 必须：
1. 先阅读 `eulerpublisher/update/container/app/format.py:parse_image_prefix` 和 `eulerpublisher/update/container/app/update.py:check_code` 的完整实现
2. 确认 CI 工作流中 `format.check_report()` 被调用时的当前工作目录和 `image-list.yml` 读取来源
3. 若需要修改 CI 工具逻辑，需在本地模拟 CI 环境进行回归测试，确保不影响已有镜像的校验
