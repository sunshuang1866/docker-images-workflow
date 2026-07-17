# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（变体）—— 根级 README 路径校验
- 新模式标题: 根级README路径校验
- 新模式症状关键词: Path Error, expected path, README.md, specification errors, appstore

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.

+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具检测到 `README.md` 在 PR diff 中，执行路径校验时判定为 FAILURE。`README.md` 是仓库根目录的纯文档文件，不包含任何应用镜像 Dockerfile、meta.yml、image-info.yml 等发布所需的制品，不在 CI 发布预检工具的预期文件路径模式内，因此被标记为路径错误。

### 与 PR 变更的关联
**直接相关。** 该 PR 的唯一变更是修改仓库根目录的 `README.md` 和 `README.en.md`（更新可用镜像 Tags 列表，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目并将 latest 标签从 sp2 升级到 sp3）。CI 的 appstore 发布预检工具扫描这些变更文件时，将根级 README 标记为不符合发布规范的路径。如果 PR 包含的是应用镜像目录下的制品文件（如 `Others/foo/1.0/Dockerfile`），则不会触发此路径校验失败。

## 修复方向

### 方向 1（置信度: 中）
本次 PR 是纯文档更新（README.md 中的 Tags 列表维护），不涉及任何应用镜像的 Dockerfile、元数据文件或构建逻辑。CI 触发了 appstore 发布规范预检，该检查对非发布制品文件（根级 README）报路径错误。两个可行的处理思路：

- **(A)** 若此 CI job 是本仓库 PR 的必检项，且纯文档 PR 不应触发 appstore 发布规范检查，则需要在 CI 编排层面（Jenkins pipeline）添加对纯文档 PR 的跳过逻辑（例如检测 diff 中是否仅包含 `*.md` 文件且无 `Dockerfile`/`meta.yml`/`image-info.yml`/`image-list.yml`，若是则跳过 appstore 预检 job）。
- **(B)** 若本仓库要求所有 PR 都通过 appstore 发布预检，则仅更新 README.md 的 PR 不应单独提交——此类文档维护应合并到包含实际应用镜像变更的 PR 中。

### 方向 2（置信度: 低）
理论上也可能是 CI 工具 `update.py` 中路径匹配逻辑存在 bug，对根级 `README.md` 的路径规范化处理不正确（例如缺少 leading `/` 的正则匹配问题）。但此方向需要审阅 `update.py` 源码中路径校验的具体实现，当前证据不支持此推断优先于方向 1。

## 需要进一步确认的点
1. Jenkins pipeline 中该 appstore 预检 job 是否对**所有 PR** 均为必检项，还是仅在特定条件下触发？若为必检项，需确认纯文档 PR 是否有预期的跳过机制。
2. `eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑具体如何实现——是白名单模式（只接受特定路径模式如 `**/Dockerfile`）还是黑名单模式（排除特定文件）？当前日志不足以确定。
3. 是否有其他类似纯文档 PR 的历史案例可作为参考（如仅修改 README 的 PR 是否也通过了 CI）？

## 修复验证要求
若采用方向 1(A)（在 CI 编排层添加纯文档 PR 跳过逻辑），code-fixer 必须在修改后验证：一个仅包含 README.md 变更的 PR 不再触发 appstore 预检 job，而包含 Dockerfile 变更的 PR 仍然正常触发。
