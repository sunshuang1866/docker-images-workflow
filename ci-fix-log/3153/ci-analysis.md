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
2026-07-14 11:28:17,839-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范检查工具（`update.py`）对 PR 中修改的 `README.md` 进行路径校验时，发现其路径不满足 appstore 上架规范的预期——工具预期的路径格式为 `/README.md`（带前导 `/`），而 diff 中检测到的路径为 `README.md`，路径格式不匹配导致校验失败。

### 与 PR 变更的关联

**PR 变更与 CI 失败存在关联，但失败性质属于 CI 工具的误判。**

PR #3153 仅修改了两个文件：
1. `README.md` — 更新基础镜像可用 tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 等条目，调整 latest 指向）
2. `README.en.md` — 与 README.md 同步更新

这是纯文档变更，不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的修改，也未新增任何镜像目录。然而，CI 流水线中包含 appstore 发布规范预检（`update.py`），该检查是针对 Docker 镜像上架的路径结构校验；当它检测到 `README.md` 在 diff 中时，将其当作一个需要审核的发布项进行路径校验，而仓库根目录的 `README.md` 不符合 appstore 规范中对镜像变更文件路径的预期格式（`/README.md`），导致校验失败。

历史上 PR #2512 系列案例显示，类似的路径校验失败曾发生在 `.claude/agents/README.md` 等文件上——CI 的 appstore 预检对非镜像文件路径存在路径格式匹配过严的问题。

## 修复方向

### 方向 1（置信度: 中）
根本原因是 `update.py` 的路径检查逻辑在处理 diff 中的文件路径时，将 `README.md`（不带前导 `/` 的相对路径）与预期格式 `/README.md`（带前导 `/` 的绝对路径）进行严格字符串比较，两者不匹配导致误报。修复方式是在 `update.py` 的路径比较逻辑中对 diff 路径统一添加前导 `/`，确保与期望格式一致。但**注意**：此修复位于 CI 工具代码（eulerpublisher），不在本仓库内，需由 CI 基础设施团队处理。

### 方向 2（置信度: 低）
若 appstore 发布规范本身要求修改 README.md 必须以特定格式（如作为某个镜像目录下的 README），则当前 PR 不应单独修改根目录 README.md。此时需要确认仓库的 README更新流程规范——是允许直接修改根 README，还是必须伴随镜像变更一起提交。

## 需要进一步确认的点

1. CI 工具 `eulerpublisher/update/container/app/update.py` 中第 270-275 行的路径校验逻辑具体如何工作——它期望的路径格式是什么，为什么 `README.md` 不被接受。
2. 本次 PR 是否还需要修改其他文件（如 `image-list.yml` 或某个 appstore 元数据文件）以通过 appstore 预检，还是根目录 README.md 的独立修改本就被允许而不应触发此检查。
3. 日志中 diff 仅列出 `README.md`，但 PR 实际还修改了 `README.en.md`——需确认 `update.py` 是否也需要校验 `README.en.md`，或者该文件不在检查范围内。
4. 历史上同类的纯文档 PR（仅修改 README 不涉及镜像变更）是否也遇到过此问题、是否有 workaround 流程。

## 修复验证要求

若修复方向涉及修改 `update.py` 的路径校验逻辑，code-fixer 需从 eulerpublisher 仓库获取 `update/container/app/update.py` 中路径比较逻辑的完整实现，确认修改后 `README.md` 能被正确匹配通过，且不影响其他镜像目录路径的正常校验（如 `AI/xxx/xx/24.03-lts-sp4/Dockerfile` 等标准 appstore 路径）。
