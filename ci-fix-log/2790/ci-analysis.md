# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（YAML / 元数据文件错误 — CI appstore 发布规范路径校验子类型）
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验逻辑）
- 失败原因: PR 仅修改了仓库根目录级别的 `README.md` 和 `README.en.md` 两个纯文档文件，CI 的 appstore 发布规范预检步骤（`update.py`）检测到变更文件中不含任何有效的镜像构建路径（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），`README.md` 被识别为不符合 appstore 发布路径规范的变更，校验失败。

### 与 PR 变更的关联
PR #2790 的 diff 仅涉及 `README.md` 和 `README.en.md` 两处文档更新（新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 等镜像 tag 条目）。CI 流水线在 x86-64 架构 job 中运行 appstore 发布规范预检，`update.py:356` 检出差异文件为 `["README.md"]`，随后在 `update.py:273` 因路径不符合 appstore 镜像发布规范而判定失败。此失败直接由本次 PR 的文档变更触发——根级 README 不满足 CI 预期的最小镜像目录结构格式。

## 修复方向

### 方向 1（置信度: 高）
此 PR 为纯文档/README 更新，不应触发 appstore 发布规范预检。需确认 CI 流水线配置是否应针对仅含根级文档变更的 PR 跳过 appstore 校验步骤。若非流水线配置可动，则需确认该 PR 的提交方式（例如是否应从跳过 CI 校验的分支合并，或采用免检标签）。

### 方向 2（置信度: 中）
若 PR 实际意图不仅是更新 README（例如 fix/2790 分支还包含实际的镜像 Dockerfile 变更但 diff 未体现），则需确认 PR 的 diff 文件是否完整——CI 日志显示检出差异仅为 `README.md`，可能存在未纳入 diff 的其他变更文件。

## 需要进一步确认的点
- 该 PR 是否本意仅为文档更新？若是，CI 的 appstore 校验步骤是否对该类 PR 不必要？
- 触发此 job 的上游 trigger（`multiarch/openeuler/trigger/openeuler-docker-images` build #2783）是否对纯文档 PR 有免检机制？
- Jenkins job 中的 `update.py` appstore 校验逻辑是否可配置跳过根级 README 文件？
