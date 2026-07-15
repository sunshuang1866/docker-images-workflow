# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: -
- 新模式症状关键词: -

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-[...]/update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-[...]/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 变更文件进行路径校验，根目录 `README.md` 的路径未能通过该校验（Description 为 `[Path Error] The expected path should be /README.md`）。PR 仅包含两个根级 README 文件（`README.md`、`README.en.md`）的文档更新，不涉及任何应用镜像目录下的文件，变更内容不符合 appstore 发布规范中要求的最小目录单元路径格式。

### 与 PR 变更的关联
PR 直接触发了该失败。本次 PR 仅修改了根目录 `README.md`（和 `README.en.md`），用于更新基础镜像的 Tags 列表（将 latest 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09` 条目，修正 `24.03-lts-sp2` 的 URL）。CI 的 appstore 发布规范检查将 `README.md` 识别为变更文件后执行路径校验，由于根级 README 不属于任何应用镜像的最小目录单元（按项目规范应为 `{场景}/{镜像名}/{版本}/{系统版本}/` 结构下的文件），校验失败。

## 修复方向

### 方向 1（置信度: 高）
根级 `README.md` 和 `README.en.md` 属于项目整体文档，不是应用镜像发布的一部分。如果本 PR 的目标仅是更新项目整体 README 文档，需确认触发 CI appstore 检查是否为预期行为——可能是 CI 的触发条件过于宽泛（所有 PR 均触发 appstore 规范校验），需调整 CI 配置使仅文档类 PR 跳过该检查。

### 方向 2（置信度: 中）
如果 appstore 规范校验要求所有变更文件都必须位于合法的镜像目录路径下，则根级 README 的修改需要搭配至少一个合法镜像目录下的文件变更，或者将 README 变更拆分到单独的文档 PR 中（使用 CI 允许的 skip 标签或分支命名约定绕过 appstore 检查）。

## 需要进一步确认的点
1. CI 日志中 `Difference` 仅列出了 `README.md`，但 PR diff 同时变更了 `README.en.md`。需确认 `README.en.md` 是否也被检查、是否通过了校验，还是 CI 工具仅报告了首个失败项。
2. `update.py:273` 的路径校验逻辑细节——具体期望的路径格式是什么？`[Path Error] The expected path should be /README.md` 中的 `/README.md` 是实际期望还是当前实际值？需查阅 `eulerpublisher` 工具对应版本源码确认。
3. 该项目是否有针对纯文档 PR 的 CI 跳过机制（如 `[skip ci]` 标签、特定分支命名等），若有则本次 PR 未正确使用该机制。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败的修复方向不涉及修改正则以匹配上游源文件。
