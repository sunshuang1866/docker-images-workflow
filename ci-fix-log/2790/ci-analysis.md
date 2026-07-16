# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用 — 已匹配已有模式)

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范预检）
- 失败原因: CI appstore 发布规范预检工具对根目录 `/README.md` 执行路径校验时判定为 FAILURE。该 PR 仅修改了根级 `README.md` 和 `README.en.md` 两个纯文档文件（更新支持的 Tags 列表），文件路径客观上就是 `/README.md`，但 CI 工具的校验逻辑仍报告 `Path Error`，行为与历史模式 11（PR #2512 系列，`.claude/README.md` 路径校验）类似。

### 与 PR 变更的关联
PR 改动仅涉及两个 README 文件的内容更新（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 三个 Tag 条目，并将 latest 标签从 `24.03-lts-sp2` 迁移到 `24.03-lts-sp3`），不涉及任何目录结构调整、Dockerfile 变更或新增镜像。该 CI 失败并非由 PR 代码变更触发，而是 CI 的 appstore 规范预检流程对根级 `README.md` 的路径校验逻辑存在问题/误报。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具 `update.py` 对根级 `README.md` 的路径校验存在误报（期望路径与实际路径一致却仍报错）。这是一个 CI 工具/infra 层面的问题，**与 PR 代码变更无关**。建议由 CI 平台维护者排查 `update.py:273` 处路径校验逻辑，或为纯文档类 PR 添加 appstore 校验豁免规则。

### 方向 2（置信度: 低）
PR 的触发方式（如分支名、标签、或 PR 模板中的某些元数据字段）导致 CI 误将此 PR 识别为 appstore 发布 PR，从而触发规范校验。实际该 PR 仅应触发文档类检查。如果是 PR 模板或分支名导致误判，需要修正 CI pipeline 的 PR 分类逻辑。

## 需要进一步确认的点
1. 为何此次仅修改根级 README 的 PR 触发了 appstore 发布规范预检？需确认 PR 的触发条件（分支名、是否勾选了 appstore 发布相关选项、PR 模板中的字段）。
2. `update.py:273` 处路径校验的具体逻辑是什么？为何 `/README.md` 的实际路径与期望路径一致却仍判定 FAILURE？
3. 是否存在 README.md 的**内容格式**要求（如必须包含特定 Front Matter 或表格结构），而校验工具错误地以 "Path Error" 的形式报告了内容问题？
4. `README.en.md` 也在 PR diff 中但未被 CI 的 `Difference` 列表列出，需确认 `update.py` 对文件类型的过滤逻辑。
