# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（部分相关）
- 新模式标题: 仓库级文件触发应用商店校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455 INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685 ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 检测到 PR 修改了仓库根目录的 `README.md`，将该文件视为 appstore 应用镜像的 README 进行路径规范校验，但由于仓库级别 `README.md` 并非 appstore 镜像实体的 README，其路径不符合 appstore 期望的子目录结构，导致校验失败。

### 与 PR 变更的关联
PR 仅修改了两个文件：`README.md` 和 `README.en.md`（更新 supported tags 列表、新增 25.09 / 24.03-lts-sp3 / 24.03-lts-sp2 条目）。这些是纯仓库文档更新，不涉及任何 Docker 镜像构建文件（Dockerfile、meta.yml、image-info.yml 等）。

失败是由 CI 工具错误地将根目录 `README.md` 纳入 appstore 镜像发布路径校验而触发的，**并非 PR 改动内容本身有误**。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的 diff 分析逻辑未过滤仓库根目录级别文件（如 `README.md`、`README.en.md`）。应在差异文件列表中排除不含有效镜像子目录路径的文件，使其不被纳入 appstore 发布规范校验。

### 方向 2（置信度: 中）
如果 CI 无法区分仓库级文件和镜像级文件，可考虑为根目录 README 建立白名单规则——根目录 `README.md` / `README.en.md` 应跳过 appstore 路径校验。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中差异文件的过滤逻辑：确认该工具是否有文件路径白名单或分类机制，以及为何根目录 `README.md` 被纳入 appstore 镜像校验。
- 历史 PR（如 #2308 `AI/diskann/README.md`）中纯文档修正是否曾触发同类校验失败，以确认这是工具回归还是长期存在的问题。

## 修复验证要求
本报告提出的修复方向涉及 CI 工具 `eulerpublisher` 的 `update.py` 逻辑变更，而非正则 patch 外部源文件，故不适用上游文件验证要求。
