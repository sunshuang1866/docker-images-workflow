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
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（文档文件），CI 的 appstore 发布规范预检在扫描变更文件时，检测到 `README.md` 位于仓库根路径。该路径不被 appstore 镜像发布目录（如 `AI/`、`Bigdata/` 等分类目录）所接纳，因此触发了 `[Path Error]`，判定该文件不符合 appstore 发布规范。

### 与 PR 变更的关联
PR 改动仅涉及根目录下两个 README 文件的标签列表更新（添加 24.03-lts-sp4、24.03-lts-sp3、25.09 等新标签），属于纯文档修改。这些变更本身是正确的——更新了基础镜像可用 tag 列表以反映上游实际发布的版本。然而，CI 的 appstore 发布规范预检将该 `README.md` 视为"发布到 appstore"的变更进行路径校验，产生了误报。

此错误与 PR 变更内容无关，是 CI 流程对纯文档 PR 的过度检查导致的。PR 不涉及任何 Dockerfile、meta.yml 或其他镜像构建相关文件。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检逻辑可能需要调整，使得仅接触根级 README 文件（`README.md`、`README.en.md` 等纯文档文件）的 PR 跳过 appstore 路径校验。这类变更不属于"发布到 appstore"的范畴。

### 方向 2（置信度: 低）
PR 日志中显示 CI 触发的 PR 编号为 #3184（分支 `fix/3153`）而非上下文中的 #3153，可能存在 PR 编号映射偏差。如果该 PR 实际意图是修复另一个 CI 问题（分支名 `fix/3153`），则可能该分支还包含额外的代码变更未在提供的 diff 中包含。此情况需要进一步确认。

## 需要进一步确认的点
1. 确认 PR 的实际变更范围是否真的仅限于 `README.md` 和 `README.en.md`，还是分支 `fix/3153` 中包含了其他未在 diff 中展示的变更。
2. 确认 CI 日志中的 PR #3184（分支 `fix/3153`）是否与实际分析的 PR #3153 是同一个 PR（可能存在编号不匹配）。
3. 确认 `update.py` 中 appstore 发布规范预检的路径白名单是否应该将根级 README 文件排除在检查范围之外。
4. 检查同类纯文档 PR 是否也曾触发相同的 appstore 路径校验失败（参考模式11历史案例）。

## 修复验证要求
（无——本报告涉及的是 CI 流程误报，不涉及正则 patch 上游源文件的操作。）
