# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.

+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）检测到 PR 修改了 `README.en.md`，该文件的路径不符合 `update.py` 中要求的规范（期望路径为 `/README.md`），导致校验失败。同时 `README.md` 也因同一条规则被标记为失败。

### 与 PR 变更的关联
PR 修改了 `README.en.md` 和 `README.md` 中的基础镜像可用 Tag 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，调整 latest 指向）。这是纯文档内容变更。CI 的 `update.py` 检测到 diff 中含有 `.md` 文件后触发路径规格校验，其中 `README.en.md` 的文件名（含 `.en` 后缀）不符合 `/README.md` 的期望路径格式，导致校验失败。

**关键判断**：此失败由 `README.en.md` 的文件名不符合 CI appstore 发布规范触发，但该文件并非 PR 新建的——它是仓库中已有的文件，PR 仅修改了其内容。这意味着该 CI 校验对该文件在此仓库中的存在本身就持否定态度，而非 PR 引入了新的违规。

## 修复方向

### 方向 1（置信度: 高）
`README.en.md` 不符合 CI appstore 路径规范。修复方案二选一：
- **方案 A**：将 `README.en.md` 的 Tag 更新内容合并到 `README.md` 中（例如用中英双语分段），然后从 PR 中移除 `README.en.md` 的修改，并将 `README.en.md` 从仓库中删除。
- **方案 B**：向 CI 维护团队申请将 `README.en.md`（仓库已有的英语版 README）加入 appstore 校验白名单，允许根目录下同时存在 `README.md` 和 `README.en.md`。

### 方向 2（置信度: 中）
检查 `update.py:273` 附近的路径校验逻辑。可能校验所有 diff 中的 `.md` 文件是否等于 `/README.md`，当列表中存在一个不匹配的文件时，整批文件均被标记失败。若 `README.md` 本身的路径应通过校验，则只要移除 `README.en.md` 的修改（使其不出现在 diff 中），`README.md` 单独的校验即可通过。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的具体校验逻辑：是逐个文件独立判断，还是整批文件统一判断？若为后者，解释了为何 `README.md` 也标记为 FAILURE。
2. 仓库中 `README.en.md` 是否在其他 PR 中也曾修改过并通过 CI？若历史上同类 PR 通过过，则此次失败可能是 CI 校验规则近期变更所致。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——此问题不涉及外部源文件正则修改）
