# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录 README 触发 Appstore 校验失败
- 新模式症状关键词: Path Error, expected path should be, README, appstore specification, eulerpublisher

## 根因分析

### 直接错误
```
2026-06-30 11:28:03,983-update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 Appstore 发布规范预检脚本对 PR 中仅修改根目录 README 文件的文档变更触发了路径校验失败。`README.en.md` 因文件名含 `.en` 后缀与预期路径 `/README.md` 不完全匹配被标记为 FAILURE；`README.md` 本身路径符合预期，但同批次检查中也被连带标记为 FAILURE，疑似检测逻辑对非镜像目录文件的处理存在误报。

### 与 PR 变更的关联
PR #2790 的 diff 仅修改了 `README.md` 和 `README.en.md` 两个根目录级文档文件，内容变更为更新镜像可用 Tags 列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目）。没有任何 Dockerfile、meta.yml、image-info.yml 或其他 Docker 镜像相关文件的变更。CI 的 Appstore 发布规范预检（`update.py`）将根目录的纯文档变更纳入了镜像发布路径校验流程，导致误报。

PR 的文档内容修改本身无误，变更内容与 PR 标题 "update readme.md" 完全一致。

## 修复方向

### 方向 1（置信度: 中）
该失败并非代码或配置错误，而是 CI 检查工具 `eulerpublisher/update/container/app/update.py` 对纯文档类 PR 的误报。此 PR 不涉及任何 Docker 镜像构建文件，应为 CI 检查逻辑的豁免场景。建议将 PR 标记为"仅文档变更"后跳过 Appstore 发布规范预检，或在 CI 触发层面对仅修改根目录文件（非镜像目录下文件）的 PR 直接跳过该检查步骤。

### 方向 2（置信度: 低）
若 CI 确实要求根目录 `README.md` 的变更也需通过 Appstore 校验，则问题可能出在 `README.en.md` 的文件名——CI 校验规则可能要求所有根目录 markdown 文件统一命名为 `README.md`，而非 `README.en.md`。此种情况下需要将英文版 README 内容合并到单一 `README.md` 中或调整 CI 校验规则以支持多语言 README 文件。

## 需要进一步确认的点
1. CI Appstore 规范预检（`update.py`）的设计意图：该检查是否仅应作用于镜像目录内的文件（如 `AI/`, `Bigdata/` 等下的 Dockerfile），还是也要求覆盖根目录文件？
2. `README.md` 本身路径 `/README.md` 与预期完全一致，为何仍被标记为 FAILURE？需确认 `update.py:273` 的检查逻辑是否在同一批次校验中存在连带标记行为。
3. 该 Appstore 发布规范预检在同类仓库的 README 变更 PR 中是否也曾触发相同失败——可检索历史 CI 运行记录确认误报频率。
4. PR 上下文中 `pr.number` 为 2790，但 CI 日志显示 `PR 2809 [sunshuang1866:fix/2790 -> master]`，需确认 CI 日志对应的是否确为 PR #2790 还是关联的修复分支 PR #2809。
