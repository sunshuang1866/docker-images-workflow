# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README触发应用校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具（`update.py`）检测到仓库根目录的 `README.md` 被修改后，将其作为应用镜像条目进行路径校验。该工具期望文件位于符合 `{category}/{image-version}/{os-version}/...` 结构的目录下，但根目录 `README.md` 不匹配任何应用镜像路径规范，导致 `[Path Error]` 校验失败。

### 与 PR 变更的关联
PR #3153 的 diff 仅涉及两个文档文件的修改（`README.md` 和 `README.en.md`），更新了可用基础镜像的 Tags 列表，属于纯文档变更。不包含任何 Dockerfile、meta.yml、image-list.yml 等应用镜像相关文件的增改。CI 的 appstore 检查不应将根目录文档文件纳入应用镜像发布规范校验范围，此失败与 PR 的实际代码变更内容无业务关联，属于 CI 工具对文档变更的误判。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，无需对本 PR 的 README 文件做任何修改。需要 CI 团队排查 `eulerpublisher/update/container/app/update.py` 中文件变更检测逻辑——当 PR 仅修改根级文档（如 `README.md`、`README.en.md`）而不包含应用镜像相关文件（Dockerfile、meta.yml 等）时，应跳过 appstore 发布规范校验，或将其排除在校验范围之外。

### 方向 2（置信度: 低）
若上述方向不成立（即 CI 工具行为符合设计预期，根目录 README.md 确实需要通过 appstore 路径校验），则可能是路径比较逻辑中存在字符串处理偏差（如相对路径 `README.md` 与绝对路径 `/README.md` 的严格比较不匹配）。需检查 `update.py` 中路径标准化逻辑。

## 需要进一步确认的点
1. 需要查看 `eulerpublisher/update/container/app/update.py:273` 附近的源代码，理解 appstore 校验工具对文件变更列表的处理逻辑，确认根目录 `README.md` 是否应被纳入校验范围。
2. 确认 PR #3184（`fix/3153` 分支，CI 日志中实际触发的 PR）是否包含除 README 之外的其他文件变更。如果 `fix/3153` 分支包含应用镜像提交，则 appstore 检查被触发是正常的，`README.md` 的路径报错可能是该检查中的误副产物。
3. 确认 `eulerpublisher/update/container/app/format.py:_parse_image_info` 中对路径结构的预期与实际校验逻辑是否对根目录文件有特殊处理。
