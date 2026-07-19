# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI路径校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification errors, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 工具的 appstore 发布规范检查器对仓库根目录下的 `README.md` 文件报告了 `Path Error`，提示"期望路径应为 `/README.md`"。然而该文件确实位于仓库根目录——即其绝对路径为 `/README.md`。CI 工具的路径校验逻辑与实际文件路径不符，属于 CI 基础设施层面的问题。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 的 Markdown 内容（更新可用基础镜像标签列表：将 `24.03-lts-sp2/latest` 变更为 `24.03-lts-sp4/latest`，并新增 sp3、25.09、sp2 条目及对应 URL），不涉及任何文件路径变更、元数据文件（meta.yml、image-info.yml、image-list.yml）修改或构建文件变更。CI 失败与此 PR 的文档内容变更无关。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，无需修改 PR 内容。可能原因：
- CI appstore 发布规范检查器（eulerpublisher）中路径比较存在前导 `/` 匹配不一致的 bug——工具提取的路径 `README.md` 与期望路径 `/README.md` 因缺少/多出前导 `/` 而不匹配
- 该检查器对于仅修改根目录文档文件（不涉及任何场景目录 `Bigdata/`、`AI/` 等下文件）的 PR 不应触发 appstore 发布规范校验，但当前逻辑对所有变更文件统一执行了该检查
- 建议向 CI 平台维护团队确认 eulerpublisher 对根目录 README 文件的路径处理逻辑是否存在缺陷

### 方向 2（置信度: 低）
若该仓库要求所有 PR（包括纯文档变更）均需通过 appstore 发布规范检查，可能的解决方向：
- 确认 appstore 发布规范是否要求根 README 的变更需配套更新特定元数据文件
- 但当前错误信息仅为路径校验失败（非内容或格式校验），且根 README.md 路径本身正确，该方向可能性较低

## 需要进一步确认的点
1. 该 CI appstore 发布规范检查是否为所有 PR（包括纯根目录文档变更）强制执行——若否，CI 配置层面可能存在触发条件过于宽泛的问题
2. CI 工具 eulerpublisher 的路径比较逻辑：`update.py:273` 处是否使用严格的字符串比较（如 `== "/README.md"`）但实际传入的路径缺失前导 `/`（即 `README.md`）
3. 同仓库中其他仅修改根目录 README 或 `.md` 文件的 PR 是否遇到过相同 CI 失败，以确认这是回归性 bug 还是已知行为
4. 若修复方向 1 被证实（CI 工具 bug），该修复需在 CI 工具（eulerpublisher）代码中进行，不在本仓库范围内
