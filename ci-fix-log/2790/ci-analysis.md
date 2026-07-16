# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685 [update.py:273] ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`eulerpublisher`) 对 `README.md` 报 "Path Error"，声称期望路径为 `/README.md`。但该文件实际存在于仓库根目录（即 `/README.md`），路径完全匹配。该报错是 CI 工具的误报（false positive），与 PR 代码变更无关。

### 与 PR 变更的关联
PR #2790 仅修改了 `README.md` 和 `README.en.md` 两个文档文件，更新了基础镜像的 Tags 列表（新增 25.09、24.03-lts-sp3 条目，修正 24.03-lts-sp2 的 URL）。PR 的变更不涉及 Dockerfile、meta.yml、image-list.yml 等应用镜像构建文件。

CI 失败来自 `eulerpublisher` 的 appstore 发布规范预检步骤，该工具对 diff 检测到的 `README.md` 进行了路径校验并误报失败。文件实际路径与期望路径一致，属于 CI 工具层面的路径比对逻辑缺陷，与 PR 改动内容无直接因果关系。

## 修复方向

### 方向 1（置信度: 低）
检查 `eulerpublisher` 中 `update.py` 的路径校验逻辑，确认是否为 diff 路径格式（`README.md`，无前导 `/`）与工具内部期望格式（`/README.md`，有前导 `/`）的前缀匹配不一致导致的误报。若是，则该问题为 CI 工具缺陷，需在 `eulerpublisher` 仓库中修复，Code Fixer 无需对 PR 分支做任何修改。

### 方向 2（置信度: 低）
若 CI 工具设计上要求 appstore 发布的 PR 必须包含至少一个 Dockerfile 或镜像元数据文件（`meta.yml`、`image-info.yml` 等）的变更，纯文档 PR 会被拒绝，则错误信息的文案具有误导性。此种情况下 PR 被拒绝为该工具的设计行为，非误报，但需联系 CI 维护团队确认具体规则。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑的具体实现，以确认是否因路径格式前缀（`/`）匹配问题导致误报。
2. CI 工具是否允许纯文档（README）变更的 PR 通过 appstore 发布规范预检——若不允许，当前的错误信息文案需改进。
3. 需要获取 `eulerpublisher` 仓库中 `update.py:222-273` 之间的完整逻辑，确认 `Difference` 检测出的文件列表如何传入路径校验并产生 "Path Error"。
