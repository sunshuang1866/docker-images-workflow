# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）检测到 `README.md` 被修改，对该文件执行路径校验时失败，报告 `[Path Error] The expected path should be /README.md`。但 PR 中的 `README.md` 实际已位于仓库根路径 `/README.md`，错误信息与实际情况存在偏差。

### 与 PR 变更的关联
本次 PR 仅修改了 `README.md` 和 `README.en.md` 两个文件（纯文档更新：更新基础镜像的 Tags 列表，将 `latest` 从 `24.03-lts-sp2` 升级为 `24.03-lts-sp3`，并新增 `25.09` 等 tag 条目）。CI 流水线中的 appstore 发布规范预检步骤扫描到 `README.md` 变更后触发了路径校验，该校验失败直接由本次 PR 改动引起。

此外，diff 中存在一个值得注意的内容问题：tag `24.03-lts-sp3` 在新版 README 中出现了**两次** —— 一次作为 `latest` 别名行的一部分（`24.03-lts-sp3, 24.03, latest`），另一次作为独立的单 tag 条目出现。虽然 CI 当前报的是路径错误而非内容重复错误，但该重复条目可能在后续检查中产生新的问题。

## 修复方向

### 方向 1（置信度: 中）
这是一个**纯文档 PR**（无 Dockerfile、meta.yml、image-info.yml 等镜像构建产物）。CI 的 appstore 发布规范预检要求 PR 包含符合规范的发布内容，仅变更 README.md 可能不被该检查接受。需确认 CI 的 appstore 检查逻辑是否会对纯文档 PR 产生误报。如果 CI 允许纯文档 PR 通过，则可能是 eulerpublisher 工具的路径比较逻辑存在 bug（如路径前缀 `a/` 与 `/` 的匹配问题）。

### 方向 2（置信度: 低）
PR diff 中 `24.03-lts-sp3` tag 出现两次（重复条目）。虽然当前 CI 报的是路径错误，但解决重复条目问题后重新触发 CI 可能有助于排查是否该内容问题间接导致了路径错误的误报。

## 需要进一步确认的点
1. CI appstore 检查（`eulerpublisher/update/container/app/update.py`）的路径校验逻辑具体如何工作——为何位于 `/README.md` 的文件会被报告路径不匹配。
2. 该 CI 流水线是否设计为允许纯文档更新的 PR 通过 appstore 发布规范预检（即没有新增镜像构建产物时是否应跳过此类检查）。
3. `README.md` 和 `README.en.md` 是否需要在某个 `image-list.yml` 或类似元数据文件中被显式注册。
