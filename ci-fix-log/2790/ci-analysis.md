# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范校验工具（`update.py`）将仓库根目录下的 `README.md` 视为 appstore 镜像提交进行路径校验。对于 appstore 镜像提交，该工具期望 README 文件位于 `<镜像名>/README.md` 等特定目录结构下；根目录 `README.md` 作为仓库级文档文件，不在任何镜像目录内，因此触发了 `[Path Error]` 校验失败。此外，日志显示 CI 仅检测到 `README.md` 变更（`Difference: ["README.md"]`），而 PR diff 实际包含 `README.en.md` 和 `README.md` 两个文件的修改，说明 CI 工具可能未完整识别所有变更文件。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 列表，新增 `24.03-lts-sp3`、`25.09` 等条目链接）。这些是仓库级文档维护，**未新增任何镜像 Dockerfile、meta.yml 或 image-info.yml**，不属于 appstore 镜像提交范畴。

CI 的 appstore 校验器（`update.py:line 273`）在检测到 `README.md` 被修改后，对其执行了镜像路径规范检查，这是 CI 工具校验范围过宽导致的问题——根目录 `README.md` 不应进入 appstore 镜像路径校验流程。

**结论：此失败与 PR 代码变更无关，属于 CI 工具行为问题。**

## 修复方向

### 方向 1（置信度: 中）
CI 的 `update.py` appstore 校验工具应在执行路径校验前，先过滤掉不属于任何镜像目录的文件（如根目录 `README.md`、`README.en.md` 等仓库级文档）。需要在 `update.py` 中增加判断逻辑：若变更文件路径不匹配 `{场景分类}/{镜像名}/` 模式，则跳过 appstore 规范校验。

### 方向 2（置信度: 低）
若 CI 工具的行为是预期设计（即任何 `README.md` 变更都会触发 appstore 校验），则问题出在本次 PR 被错误标识为 appstore 发布型 PR，或因根目录 README.md 中包含的镜列表 Tag 链接被误识别为镜像发布信息。需要检查 CI trigger 层对 PR 类型的判断逻辑。

## 需要进一步确认的点
1. CI 工具 `update.py` 的 `line 273` 附近代码：appstore 校验的触发条件是什么？是否对根目录文件有排除逻辑？
2. 为何 CI 日志中 `Difference` 仅列出 `README.md` 一个文件，而 PR diff 实际修改了两个文件（`README.md` + `README.en.md`）？需确认 CI 的 git diff 逻辑是否存在遗漏。
3. 该 CI job（`x86-64/openeuler-docker-images`）是否负责处理 appstore 发布校验之外的构建任务？需要确认 PR #2790 是否应该触发该 job。
