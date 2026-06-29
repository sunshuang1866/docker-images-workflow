# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.

| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+

Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范检查）
- 失败原因: CI 的 appstore 发布规范校验针对 PR diff 中的文件进行路径合法性检查，仓库根目录下的 `README.md` 和 `README.en.md` 不是镜像文件目录下的 README，不满足 appstore 镜像发布规范的路径格式要求，校验工具期望这些文件位于某个镜像目录内（如 `<image>/README.md`），而非仓库根层级。

### 与 PR 变更的关联
**直接关联**。PR #2790 仅修改了仓库根目录的两个 README 文件（`README.md` 和 `README.en.md`），将 Tag 列表从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，并新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 三条 Tag 记录。这两个文件出现在 diff 中后被 CI 的 appstore 发布规范校验扫描到，校验工具不认可以仓库根目录的 README 文件作为镜像发布路径，因此报路径错误。

## 修复方向

### 方向 1（置信度: 高）
根本问题在于 CI 的 appstore 发布规范校验错误地将仓库级文档变更纳入了镜像发布路径检查。应在 CI 校验工具（`update.py` 的路径检查逻辑）中排除仓库根目录下的非镜像文件（如 `README.md`、`README.en.md`、`.gitignore` 等），或在校验前过滤掉不位于镜像子目录内的文件。此修复涉及 CI 校验工具逻辑，而非 PR 内容本身。

### 方向 2（置信度: 中）
如果仓库规范要求镜像 README 文件必须位于特定子目录（如 `{image-version}/{os-version}/README.md`），且根目录 README 不应出现在 appstore 发布流程中，则需要在 CI 校验逻辑中明确区分"仓库级文档"和"镜像级文档"，前者直接跳过 appstore 路径校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑具体是如何判断文件路径合法性的，需确认其过滤规则。
2. 根据项目规范，仓库根目录的 `README.md` / `README.en.md` 是否应该被 appstore 发布规范校验所覆盖，还是这些文件应完全排除在外。
3. 历史上类似 PR（如 #2512 的 `.claude/agents/README.md` 路径校验失败）是如何修复的——是调整了文件路径还是修改了校验规则，可作为修复参考。

## 修复验证要求
因修复方向涉及修改 CI 校验工具逻辑（而非正则需要从上游拉取验证），无需额外验证步骤。如果选择方向 2，建议在修改后对以下场景做回归测试：(1) 纯根目录文件变更的 PR；(2) 镜像目录内 README 变更的 PR；(3) 同时包含根目录和镜像目录变更的 PR。
