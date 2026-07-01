# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检器在检测 PR 变更文件时，将仓库根目录的 `README.md` 和 `README.en.md` 纳入了 appstore 镜像发布路径校验流程。这两个文件是项目级文档，不隶属于任何具体镜像目录，不满足 appstore 对镜像 README 文件的路径格式要求（期望路径形如 `{category}/{image-name}/.../README.md`），导致路径校验失败。

### 与 PR 变更的关联
PR 的改动仅限于更新两个根目录 README 文件中的「可用镜像 Tags」列表（新增 24.03-lts-sp3、25.09 等 tag 条目，重新排序）。改动内容本身正确，属于常规文档维护。CI 失败并非由 PR 改动内容引起，而是 CI 工具 `update.py` 的 appstore 路径校验逻辑未区分"仓库根目录的项目级 README"与"具体镜像目录的 appstore README"，将所有被修改的 README 文件无差别纳入 appstore 路径检查。

## 修复方向

### 方向 1（置信度: 高）
在 `eulerpublisher/update/container/app/update.py` 的 appstore 规范检查逻辑中，增加对仓库根目录级文件（`/README.md`、`/README.en.md` 等）的豁免规则，使其不触发 appstore 镜像路径校验。这些文件属于项目整体文档，不属于任何具体镜像的 appstore 发布范畴，不应受镜像目录路径规范约束。

### 方向 2（置信度: 中）
如果修改 CI 脚本不可行，可将 PR 的 README 改动与镜像相关的改动分开提交：先单独提交镜像目录内的变更通过 CI，再提交纯文档变更。但此方向属于规避而非修复，不推荐。

## 需要进一步确认的点
- CI 工具 `update.py` 中 appstore 路径校验的豁免/白名单机制是否存在，以及如何配置。
- 该 CI 检查是否仅在 PR 包含非 README 文件时跳过根目录文件，还是无条件检查所有变更文件。
- PR #2512 中 `.claude/README.md` 的同类路径校验失败是否已修复，修复方式是什么，可作为参考。
