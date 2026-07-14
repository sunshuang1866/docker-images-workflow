# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发应用商店校验
- 新模式症状关键词: [Path Error], The expected path should be, README.md, appstore, FAILURE

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具（`eulerpublisher`）检测到 PR diff 中仅有根目录的 `README.md` 变更，对其执行了应用商店镜像路径校验。由于 `README.md` 是项目根级文档文件，不符合应用镜像的层级路径规范（如 `{category}/{app}/{version}/{os}/Dockerfile`），校验工具无法将其归类为有效的应用商店发布内容，报告路径错误。

### 与 PR 变更的关联
**PR 直接触发了此失败**，但并非 PR 内容有误。本 PR 仅修改了根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 列表，将 `24.03-lts-sp2` 替换为 `24.03-lts-sp4` 并新增 `24.03-lts-sp3`、`25.09` 条目），属于纯文档更新。CI 的 appstore 发布校验 pipeline 对纯文档 PR 进行了不应有的路径校验，导致误报 FAILURE。PR 的文档变更本身没有语法错误、链接错误或内容问题。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 校验流程应在执行路径校验前先判断 PR 变更文件类型：若 diff 仅包含项目根级文档文件（`README.md`、`README.en.md`、`CONTRIBUTING.md` 等），跳过应用商店路径规范校验，允许直接通过。这需要修改 CI 编排逻辑（`eulerpublisher/update/container/app/update.py` 或触发层 job 配置）。

### 方向 2（置信度: 低）
若 CI 工具不支持按文件类型跳过校验，可通过 CI 触发条件过滤：当 PR 仅修改根级文档文件时不触发 appstore 校验 job，改用其他轻量级文档校验（如 markdown lint）。此方法需要修改 CI pipeline 的 trigger 条件。

## 需要进一步确认的点
1. 确认 appstore 校验 pipeline 的触发条件：是否所有 PR 都会触发该校验，还是仅包含特定目录变更的 PR？
2. 确认 `eulerpublisher/update/container/app/update.py:273` 处的路径校验逻辑：是否已有文件过滤机制但未覆盖根级 README？
3. CI 日志中显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，但上下文报告 PR 编号为 #3153。需确认此 CI 运行是否来自正确的 PR，以及 #3153 和 #3184 之间的关系（#3184 的分支名为 `fix/3153`，可能是为修复 #3153 问题而创建的 PR，CI 日志中的 `Difference: ["README.md"]` 与此 PR 的 diff 内容一致）。

## 修复验证要求
无需验证。此失败属于 CI 基础设施（appstore 校验 pipeline 误报），PR 的文档变更本身无需修改。若后续选择修改 CI 工具校验逻辑以允许纯文档 PR 通过，需在 CI 环境中验证修改后的 `update.py` 确实能跳过根级文档文件的路径校验。
