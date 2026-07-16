# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对本 PR 变更的仓库根目录 `README.md` 文件执行了 appstore 镜像路径校验，校验器将路径 `README.md` 与期望格式 `/README.md`（带前导斜杠）进行比较后判定为 FAILURE。该 PR 仅包含两个 README 文档文件的标签列表更新，不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 的变更，不是镜像发布 PR，不应触发 appstore 路径规范检查。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的基础镜像可用 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，将 `latest` 别名从 sp2 更新到 sp4），属于纯文档更新。失败原因在于 CI 流水线的 appstore 预检步骤未正确区分"文档 PR"与"镜像发布 PR"，对仓库根目录的文档文件错误地执行了镜像路径校验。

## 修复方向

### 方向 1（置信度: 高）
该失败为 CI 基础设施配置问题，不是本 PR 代码变更导致。需要在 CI 流水线中增加判断逻辑：当 PR 仅包含文档文件（如仓库根目录 `README.md`、`README.en.md`）变更且不涉及任何镜像目录（`Bigdata/`、`AI/`、`Database/` 等）时，跳过 appstore 发布规范预检步骤。Code Fixer 无需对本 PR 的 Dockerfile 或 README 内容做任何修改。

### 方向 2（置信度: 低）
如果 CI 工具无法新增 docs-only PR 的跳过逻辑，可考虑在仓库根目录的 README 文件变更时不触发 appstore 检查（即 CI 侧修改 trigger 条件，仅当 `image-list.yml`、`meta.yml`、`image-info.yml` 或 `Dockerfile` 文件变更时才执行 appstore 预检）。

## 需要进一步确认的点
1. CI 流水线中 appstore 预检步骤的触发条件是什么——是检测所有文件变更还是仅检测特定文件模式。
2. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现：为何 `README.md` 被纳入检查范围，以及期望路径 `/README.md` 的规则定义位置。

## 修复验证要求
不适用。本失败为 infra-error，无需对代码做任何修改。
