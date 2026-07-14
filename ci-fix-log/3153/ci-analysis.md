# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根文档触发应用检查
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py:273, specification errors for releasing on appstore

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`（非 PR 变更文件）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）扫描 PR 变更文件时发现 `README.md`，将其当作 appstore 上架候选文件进行路径校验，但根级 `README.md` 不属于任何 appstore 镜像目录结构（标准格式为 `{category}/{image-version}/{os-version}/`），导致路径校验失败。

### 与 PR 变更的关联

**直接相关**。PR 仅修改了根级文档文件 `README.md` 和 `README.en.md`（更新可用基础镜像 tag 列表），不涉及任何 Dockerfile 或镜像目录变更。CI 的 appstore 预检工具（`eulerpublisher/update/container/app/update.py`）将此类纯文档变更误判为 appstore 上架请求，并按 appstore 路径规范进行校验，导致误报。

PR diff 中的变更：
- `README.md`：更新基础镜像 tag 行，新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` tag 条目
- `README.en.md`：同上（英文版）

两个变更文件均为根级纯文档修改，不涉及任何镜像构建。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具 `eulerpublisher/update/container/app/update.py` 在检测到仅包含根级文档变更（无镜像目录变更）的 PR 时应跳过 appstore 路径校验。需在 `update.py` 中增加判断逻辑：若 PR 变更文件列表仅包含根级非镜像目录文件（如 `README.md`、`README.en.md`、`.gitignore` 等），则不执行 appstore 规范校验，直接放行。

### 方向 2（置信度: 低）
若 CI 工具不支持跳过逻辑，可考虑在仓库中为纯文档变更 PR 添加特殊标记或 label（如 `skip-appstore-check`），CI 根据该标记跳过 `update.py` 的 appstore 校验步骤。

## 需要进一步确认的点

1. `eulerpublisher/update/container/app/update.py` 中第 273 行前后的路径校验逻辑：确认该工具如何判断变更文件路径是否符合 appstore 规范，以及是否已有"跳过纯文档 PR"的机制
2. 确认 CI 触发条件：当前 PR 是否因为仅修改根级 README 文件而被错误路由到 appstore 检查流水线，还是所有 PR 都会无条件触发此检查
3. 上下文中的 PR 编号（#3153）与 CI 日志中的 PR 编号（#3184）存在不一致，需确认本次分析的目标 PR 与实际触发 CI 的 PR 是否为同一个（日志显示触发分支为 `sunshuang1866:fix/3153 -> master`，推测 #3184 为 #3153 的修复/跟进 PR）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）

不适用。本次修复方向不涉及正则 patch 外部源文件。
