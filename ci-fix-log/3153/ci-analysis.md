# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径格式校验误报
- 新模式症状关键词: Path Error, expected path, appstore specification, README.md, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范校验阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 的 `eulerpublisher` appstore 校验工具检测到 `README.md` 被修改后，对其路径格式进行校验。工具期望的路径格式为 `/README.md`（带前导斜杠），但 diff 提取的路径为 `README.md`（无前导斜杠），导致路径格式不匹配校验失败。PR 仅包含纯文档变更（更新基础镜像 tags 列表），不含任何需要 appstore 路径校验的应用镜像文件，此次校验属于工具对根级文档文件的不当拦截。

### 与 PR 变更的关联
PR #3153 仅修改了根目录下的 `README.md` 和 `README.en.md`（更新可用基础镜像 tags 列表）。这些是纯文档变更，不涉及任何应用镜像 Dockerfile、meta.yml、image-info.yml 等需要 appstore 发布规范校验的文件。CI 失败是由校验工具自身的路径格式化问题触发，与 PR 的文档内容变更本身无逻辑关联。

## 修复方向

### 方向 1（置信度: 中）
CI 的 `eulerpublisher` appstore 校验工具在提取变更文件路径时未添加前导 `/`，导致与预期的 `/README.md` 格式不匹配。应在 CI 工具的路径提取逻辑中将提取到的相对路径统一加前导 `/` 后再与期望路径比较。或者，appstore 发布规范校验应仅对应用镜像目录（Bigdata/、AI/、Database/ 等）下的文件执行，跳过根级 README.md 等纯项目级文档文件的路径校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径提取和校验的具体逻辑，确认路径格式化的缺失是否确实在提取阶段还是比较阶段。
2. 确认 CI appstore 校验的预期覆盖范围——是否应对根级 README.md 执行路径校验，还是应限制在应用镜像目录内。
3. PR #3184（`sunshuang1866:fix/3153 -> master`）是 CI 实际触发的 PR，其 diff 可能与原始 PR #3153 存在差异，如有额外变更文件也需确认其路径格式。
