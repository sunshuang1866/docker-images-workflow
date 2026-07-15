# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档变更触发路径校验拒绝
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification errors, update.py

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 修改了根目录 `README.md`，该文件不在 appstore 镜像发布规范的预期路径清单中，触发 `[Path Error]` 校验失败。PR 3153 是纯文档变更（仅更新根目录 README.md 和 README.en.md 中的基础镜像标签列表），而 CI 流水线不会区分"文档 PR"与"镜像 PR"，对所有 PR 均执行 appstore 路径校验，导致误报。

### 与 PR 变更的关联
- **直接关联**。PR 的唯一改动是 `README.md` 和 `README.en.md` 中基础镜像可用标签的更新（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，更新 latest 指向）。CI 的 `update.py` 工具在处理 diff 时发现 `README.md` 无法映射到任何 appstore 镜像条目（根级文档不在 `Bigdata/`、`AI/` 等场景目录下，也不在 `image-list.yml` 中），遂报路径错误。
- 此问题与历史 模式11（PR #2512 中 `.claude/agents/README.md` 路径不符合规范）属同类 CI 校验逻辑，但当前案例涉及的是根目录文档文件，而非子目录路径层级问题。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 路径校验步骤（`update.py` 中的 diff 文件路径验证逻辑）需要增加对根目录文档文件（如 `README.md`、`README.en.md`）的白名单豁免。当 PR 的 diff 仅包含白名单中的文件时，跳过 appstore 规范检查。此问题属 CI 基础设施逻辑缺陷，与 PR 代码变更内容无关，PR 作者无需修改 Dockerfile 或 README 内容。

### 方向 2（置信度: 中）
如果白名单豁免短期内无法在 CI 管道中实施，可将 `README.md` 和 `README.en.md` 注册到 CI appstore 校验配置中（如 `image-list.yml` 或等效的 manifest 文件），使校验工具接受这些路径。但此方案仅为临时绕过，不符合 `README.md` 作为仓库级文档而非镜像级文档的语义。

## 需要进一步确认的点
1. CI 工具 `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——如何区分"应在 appstore 发布的镜像文件"与"仓库元数据文档文件"。
2. 根目录中是否已有等效的白名单机制或豁免配置（如 `.ci-ignore`、`check-config.yml` 等），以及为何未对 `README.md` 生效。
3. 该 CI 错误是否在之前的同类纯文档变更 PR 中出现过相同症状（对比历史 PR 是否有先例），以判断此问题是否为本次 PR 新触发的 CI 配置变更所致。

## 修复验证要求
若不涉及对上游/第三方源文件的补丁或正则修改，则无需额外验证。
