# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR触发appstore校验
- 新模式症状关键词: Path Error, README.md, expected path, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171 - INFO: Difference: [ "README.md" ]
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 对 PR 中变更的 `README.md` 进行了路径校验，判定其"不在期望路径"。该 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档变更），但 appstore 校验工具未对根级文档做豁免处理，仍按镜像目录结构 (`{category}/{name}/{version}/{os}/`) 规则进行检查，导致误报。

### 与 PR 变更的关联
PR 变更仅涉及仓库根目录的 `README.md` 和 `README.en.md`，更新了基础镜像可用 Tags 列表（如新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`，补回 `24.03-lts-sp2` 条目，并将 `latest` 标签从 sp2 迁移到 sp4）。这些变更不涉及任何镜像目录（非 `Bigdata/`、`AI/`、`Cloud/` 等场景子目录）或 Dockerfile，与 appstore 发布无关。CI 失败并非由 PR 代码变更的内容错误引起，而是 CI 校验工具错误地将针对镜像目录的路径规则应用到了根级文档上。

此外，日志中 CI 构建由 **PR #3184** (`sunshuang1866:fix/3153 → master`) 触发，而非 PR #3153 本身。推测 #3153 首次提交时即触发相同失败，随后通过 #3184 尝试修复但未解决校验工具层面的路径匹配问题。

## 修复方向

### 方向 1（置信度: 低）
CI 流水线配置或 `update.py` 校验工具缺少对根级文档文件（`README.md`、`README.en.md` 等）的豁免逻辑。修复方向是调整 CI 校验脚本，在路径检查阶段跳过仓库根目录的非镜像文件，使其不触发 appstore 发布规范校验。但此方向涉及 CI 基础设施代码（非本仓库 Dockerfile），需确认该工具的维护归属。

### 方向 2（置信度: 低）
若 CI 校验工具的逻辑是"所有 PR 必须包含至少一个镜像目录的变更"才可通过，则该纯文档 PR 本身不被 CI 流水线允许。此时需要确认此类文档变更是否应通过其他渠道（如 wiki、独立文档仓库）提交，而非混入镜像构建 PR 流水线。

## 需要进一步确认的点
1. **确认 CI 日志来源**：提供的日志触发自 PR #3184（`fix/3153`），而非 PR #3153 本身。需获取 PR #3153 的原始 CI 日志以确认两次失败是否一致。
2. **确认 PR #3184 的 diff**：PR #3184 的分支名 `fix/3153` 暗示其为 PR #3153 的修复尝试，需要获取其 diff 以了解尝试了何种修复及为何仍失败。
3. **确认 `update.py` 的路径校验逻辑**：需查阅 `eulerpublisher/update/container/app/update.py` 中第 220-275 行附近的路径校验逻辑，确认其是否对所有变更文件一视同仁地应用镜像目录结构规则，以及是否存在根级文件的豁免白名单。
4. **确认 CI 流水线配置**：需了解该 workflow 是否正确配置了按 PR 类型（docs vs image）选择不同校验步骤，即 appstore 校验是否应仅对有镜像目录变更的 PR 执行。
5. **确认 docs-only PR 的预期 CI 行为**：向 CI 流水线维护方确认，仅文档变更的 PR 是否应通过 appstore 校验流水线，以及是否支持纯文档 PR 合并。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——该 PR 仅涉及 README 文档变更，且失败原因为 CI 工具路径校验误报，不涉及任何 Dockerfile 或上游源码的正则 patch。
