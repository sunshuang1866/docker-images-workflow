# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级README路径误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）检测到 PR 修改了 `README.md`，并对其执行路径校验。该文件位于仓库根目录 `/README.md`，不属于任何应用镜像子目录（如 `AI/`、`Bigdata/` 等），不包含 Dockerfile 或 `meta.yml`，因而不应被 appstore 镜像发布校验所覆盖。CI 工具将非镜像的文档文件误纳入校验范围，导致路径校验失败。

### 与 PR 变更的关联
PR #2790 仅修改了 `README.md` 和 `README.en.md`（仓库根目录的文档文件），内容变更包括：
1. 将 `latest` 标签对应的版本从 24.03-lts-sp2 更新为 24.03-lts-sp3
2. 新增标签条目：25.09、24.03-lts-sp3、24.03-lts-sp2
3. 重新编排标签列表

PR 中未修改任何 Dockerfile、`meta.yml`、`image-info.yml` 或 `image-list.yml`，不应触发 appstore 镜像发布校验。CI 将根级 README 文档的变更误路由至 appstore 发布预检流水线，与本 PR 的实际改动内容无关。

**附注**：PR diff 中存在一个内容问题——`24.03-lts-sp3` 标签在列表中出现了两次（一次作为 `[24.03-lts-sp3, 24.03, latest]`，另一次单独作为 `[24.03-lts-sp3]`），但此内容重复与 PATH 类型校验错误无关。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线或 `eulerpublisher` 工具应在 appstore 发布校验阶段排除仓库根目录的纯文档文件（如 `README.md`、`README.en.md`）。当 PR 仅涉及根级文档变更（无任何图像目录文件改动）时，应跳过 appstore 规范检查步骤，直接标记为通过。这是 CI 配置/工具逻辑问题，与 PR 代码变更无关。

### 方向 2（置信度: 低）
若 `eulerpublisher` 的路径校验逻辑依赖文件路径模式匹配（如仅允许 `/{category}/{image}/{version}/{os-version}/Dockerfile` 格式的路径），且根级文件无对应的排除规则，则需在 `update.py` 中为仓库根目录文件添加白名单或跳过逻辑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——确认其是否对根级非镜像文件已有排除规则，以及为何本 PR 触发了该规则
2. 过往仅修改 `README.md` 的 PR 是否同样触发过此 CI 失败——若历史同类 PR 可以正常通过，则可能与本 PR 的 diff 内容或 CI 工具版本变更有关，需要对比排查
3. 本 PR 引入的 `24.03-lts-sp3` 重复条目是否与路径校验逻辑产生意料之外的交互（虽然错误类型为 Path Error 而非 Content Error）

## 修复验证要求
由于此失败归类为 `infra-error`，修复方向不涉及具体代码补丁或正则匹配。code-fixer 无需执行上游文件验证。如需修复，应在 CI 流水线配置或 `eulerpublisher` 工具源码中调整，无需对 Docker 镜像仓库内的文件做任何变更。
