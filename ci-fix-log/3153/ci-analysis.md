# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI 根级 README 路径校验误报
- 新模式症状关键词: Path Error, expected path should be, /README.md, eulerpublisher, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`:273
- 失败原因: CI appstore 发布规范预检工具 (`eulerpublisher`) 对 PR 中变更的文件执行路径校验，检测到根层级 `README.md` 发生变更后，判定其不满足 appstore 发布路径规范（工具期望的路径格式与根级 `/README.md` 不符），导致 FAILURE。

### 与 PR 变更的关联
PR 仅修改了两个根级文件：`README.md` 和 `README.en.md`，内容为文档性更新（将基础镜像的可用 Tags 列表中的 `latest`/`24.03` 条目从 `24.03-lts-sp1` 更新为 `24.03-lts-sp4`，并新增 `sp3`、`sp2`、`25.09` 条目）。这些变更是纯文档修正，不涉及任何 Dockerfile、meta.yml、image-info.yml 或应用镜像目录结构。CI 工具对所有变更文件运行 appstore 发布路径校验，根级文档文件不在该工具预期的路径模式内，因此被误报为路径错误。**该失败与 PR 变更内容无关，系 CI 校验工具对根级文档的路径检查逻辑缺陷。**

## 修复方向

### 方向 1（置信度: 低）
CI 工具的 appstore 路径校验逻辑可能未正确处理根级非应用镜像文件（如 repo 主 README）的变更。根级文档不应经过应用镜像目录结构的路径校验。如在 CI 工具端有控制逻辑（如白名单文件列表），可将根级 `README.md`、`README.en.md` 排除在 appstore 路径校验范围之外。但这属于 CI 基础设施端修复，Code Fixer 无需处理。

## 需要进一步确认的点
- CI 日志仅提供了 `x86-64` 架构 job 的日志，虽当前失败表现为路径校验问题而非架构构建问题，但需确认是否同一 PR 在其他架构 job（如 aarch64）上也有相同失败
- `eulerpublisher/update/container/app/update.py`:273 中具体路径校验逻辑需要审阅，以确认是否为工具 bug（将根级 README 误判为应用镜像文件），或是否有合法的路径白名单配置
- 确认该 CI 校验是否在 PR 仅包含根级文档变更时确实应被跳过

## 修复验证要求
此失败为 CI 工具（eulerpublisher）在根级 README 文件上的路径校验误判，PR 代码变更本身无问题，无需 Code Fixer 对代码进行修复。若后续确认需修改 CI 工具侧逻辑（如 update.py 需增加根级文件白名单），则需由 CI 维护者在 eulerpublisher 工具仓库中修改并验证。
