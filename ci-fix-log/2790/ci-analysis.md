# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（CI appstore 发布规范预检）
- 新模式标题: (不适用——匹配已有模式11)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 中唯一变更的文件 `README.md`（根目录）进行路径校验时，报出 "Path Error"，声称期望路径为 `/README.md`。然而 `README.md` 实际就位于仓库根目录 `/README.md`，该路径校验报错疑似 CI 工具的误报。

### 与 PR 变更的关联
- PR 仅修改了两个根级文件：`README.md` 和 `README.en.md`，内容为更新基础镜像 Tags 列表（新增 `24.03-lts-sp3` 和 `25.09` 条目，修正原有 24.03-lts-sp2 的链接 URL）
- 变更中不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等与镜像构建/发布直接相关的文件
- CI 报错并非由 PR 的文档内容变更触发的代码逻辑错误，而是 CI 校验工具对非镜像文件的路径检查机制产出了误报

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检工具对根目录 `README.md` 的路径校验存在过度严格或 Bug：实际路径 `/README.md` 与期望路径 `/README.md` 一致，但仍然判定 FAILURE。需要排查 `eulerpublisher/update/container/app/update.py` 中路径比较逻辑（可能为字符串比较时缺少规范化导致 `README.md` vs `/README.md` 的前缀 `/` 不匹配），或确认该 CI 校验是否应当对纯文档类 PR 豁免检查。

### 方向 2（置信度: 低）
PR 仅变更根级 README 文档，不包含任何镜像新增/修改。CI appstore 校验步骤可能根本不应在此类 PR 的 pipeline 中被触发。如果这是 CI 流水线编排层面的问题，则需调整 trigger/编排层逻辑，使纯文档 PR 跳过 appstore 规范检查。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑——具体的比较条件和错误触发情境
2. CI 流水线中 appstore 规范检查步骤的触发条件——是否对纯文档（README-only）PR 已有豁免逻辑
3. 同类历史案例（模式11 中 PR #2512 的 `.claude/` 路径问题）是否在 CI 工具代码中已修复，或是否存在回归

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——此问题涉及 CI 工具内部逻辑（`eulerpublisher` 包），不涉及第三方/上游源文件的正则匹配。
