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
2026-06-30 11:28:09,089-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检（update.py）将仓库根目录的 `README.md` 和 `README.en.md` 视为应用镜像提交文件进行路径校验，但这两个文件是仓库级别的文档（非应用镜像 README），不符合 appstore 期望的 `{category}/{image}/README.md` 层级结构，因此被报告为 [Path Error]。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中的镜像 Tag 信息（添加 24.03-lts-sp3、25.09 等新 Tag 条目的文档链接）。因为 PR 未涉及任何 Dockerfile、meta.yml 或 image-info.yml，CI 无需对 README 文档变更执行 appstore 路径校验。**该失败与 PR 变更内容无关**，属于 CI 流程对非应用镜像文件变更的误报。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 预检逻辑应跳过仓库根目录的 README 文件（`README.md`、`README.en.md`）。这些文件是仓库本身的文档，不属于任何应用镜像的最小目录单元，不应受 appstore 路径规范约束。可以在 `update.py` 的变更文件检测环节增加过滤条件，排除根层级的 README 文件。

### 方向 2（置信度: 低）
如果 CI 流程设计上要求所有 PR 文件必须通过 appstore 预检（无法跳过），则可以将 README 变更拆分到另一个不触发 appstore 预检的 CI 流程中处理。

## 需要进一步确认的点
- CI appstore 预检脚本（`eulerpublisher/update/container/app/update.py`）中对变更文件的过滤逻辑：是否有白名单/黑名单机制允许跳过非镜像目录的文件。
- 该 CI 触发是否对根目录 README 文件的变更是预期行为还是历史遗留问题（类似模式11 中 `.claude/README.md` 被误检的案例）。
