# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR遭CI误检
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...update.py[line:356]-INFO: Difference: ["README.md"]
...
2026-07-14 11:28:17,839-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/home/jenkins/agent-working-dir/workspace/multiarch/openeuler/x86-64/openeuler-docker-images/eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 流水线对**所有 PR**（无论是否涉及应用镜像发布）均执行了 `eulerpublisher` 的 appstore 发布规范预检。本 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 tag 列表的文档），不包含任何应用镜像发布所需的文件（Dockerfile、meta.yml、image-info.yml 等）。CI 的 appstore 路径校验工具将根目录文档文件 `README.md` 纳入检查范围，但其路径格式（缺少前导 `/` 或不属于 appstore 预期路径模式）未通过校验，返回 `[Path Error] The expected path should be /README.md`。

### 与 PR 变更的关联
PR 仅做了以下改动——更新两个 README 文件中基础镜像的可用 tag 列表：
- `README.md`: 将 `24.03-lts-sp2, 24.03, latest` 指向的链接从 SP1 修正为 SP4，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 三条 tag 条目
- `README.en.md`: 同上

这些改动是纯文档修缮，完全合法且不涉及任何需要 appstore 发布的镜像文件。CI 失败与 PR 改动内容**无因果关联**——即使改动内容完全正确，CI 的 appstore 预检步骤仍会因为 `README.md` 不在其预期的路径格式列表中而失败。这是一个 CI 基础设施层面的问题：appstore 预检不应覆盖纯文档类 PR。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中 `eulerpublisher` 的 appstore 规范预检应增加文件类型/路径过滤逻辑：当 PR 仅修改根级文档文件（如 `README.md`、`README.en.md`）而未触及任何应用镜像目录下的构建文件时，应**跳过** appstore 发布规范检查，直接放行。当前行为是 CI 将此 PR 误判为需要审核的 appstore 发布，属于 CI 配置/逻辑缺陷，应由 CI 平台侧修正。

### 方向 2（置信度: 低）
若 CI 平台侧暂时无法调整预检逻辑，可将本 PR 合入时的 CI 检查改为手动跳过 appstore 项，或在 PR 中随文档修改附上一个空 commit 触发 CI 豁免路径。此方向为临时规避手段，不应作为长期方案。

## 需要进一步确认的点
1. CI 的 `eulerpublisher/update/container/app/update.py` 中 `Difference` 的检测逻辑——为何只检测到 `README.md` 而忽略了同样被修改的 `README.en.md`，这可能影响对 CI 检测逻辑的完整理解。
2. 确认 CI 流水线的 appstore 预检是否对所有 PR 无差别执行（从日志看确实如此），还是仅对特定来源分支/标签触发。如果是无差别执行，确认是否有计划增加 PR 分类逻辑。
3. 确认 `[Path Error] The expected path should be /README.md` 中的格式化差异（有无前导 `/`）是 CI 工具的硬性校验规则还是显示层面的问题——这会影响后续 CI 侧修复的精确方式。
