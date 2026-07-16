# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检流程检测到 PR 修改了根目录下的 `README.md`，但该文件的路径被标记为 `[Path Error]`——CI 校验工具期望的路径为 `/README.md`，而实际变更文件（根目录的 `README.md`）在 diff 检测中被识别后，校验工具判定其不符合 appstore 镜像发布规范所要求的路径格式。

### 与 PR 变更的关联

**PR 与失败直接相关，但属于 CI 校验策略问题**：
- PR #3153 的变更**仅涉及根目录下两个 README 文件**（`README.md` 和 `README.en.md`），内容是更新基础镜像可用 tags 列表。没有任何 Dockerfile、meta.yml、image-info.yml 或其他镜像构建相关文件的变更。
- CI 工作流（x86-64 架构 job）在执行 appstore 发布规范预检时，将根目录 `README.md` 的变更纳入了镜像发布路径校验，并判定路径不符合规范。
- 这是一个**纯文档 PR**，不应触发镜像级别的 appstore 路径校验。CI 工具 `eulerpublisher` 的 `update.py` 在校验变更文件时，未能区分"仓库根目录文档变更"与"应用镜像目录文件变更"，将根目录 README 误判为镜像发布相关文件。

## 修复方向

### 方向 1（置信度: 中）
此失败由 CI 端 `eulerpublisher` 工具的 appstore 规范校验逻辑引起——它未将仓库根目录下的纯文档文件（如 `README.md`、`README.en.md`）排除在校验范围之外。**如果需要在 PR 侧修复**，可考虑调整 PR 的变更范围，例如仅通过单独的文档更新流程来更新 README（而非通过标准 Docker 镜像 CI 流水线），但这属于流程层面的调整，不涉及 Dockerfile 或构建逻辑的修改。

### 方向 2（置信度: 低）
检查 CI 校验工具 `eulerpublisher/update/container/app/update.py` 中 diff 检测与路径校验的逻辑：该工具在检测到 `README.md` 变更后将其路径误判，可能与 `git diff` 输出的路径格式（带/不带前导 `/`）有关。但此方向需要在 CI 工具侧修复，超出 PR 提交者的可控范围。

## 需要进一步确认的点
1. CI 的 appstore 路径校验是否正确忽略了仓库根目录的非镜像文件（如 `README.md`、`README.en.md`、`.github/` 等）——需要确认这是 CI 工具的已知行为还是新引入的回归。
2. 该 PR 对应的分支 `fix/3153` 是否在 CI 日志中触发了正确的 job（日志显示触发了 PR #3184 的构建，需确认 #3153 与 #3184 的关系以及是否混入了其他变更）。
3. 需要确认 `eulerpublisher` 工具在 `update.py:273` 处路径校验逻辑的具体条件——错误信息 "The expected path should be /README.md" 中，脚本比较的实际值和期望值分别是什么，是否存在路径格式规范化的问题（如 `README.md` vs `/README.md`）。

## 修复验证要求
无需额外验证。此 PR 无 Dockerfile 或构建逻辑变更，CI 失败源于工具对纯文档 PR 的误校验。
