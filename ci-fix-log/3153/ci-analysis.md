# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI appstore 发布规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新），但 CI 的 appstore 发布规范检查器对所有变更文件进行路径校验，将根级 `README.md` 与 appstore 镜像路径规范进行比对，判定路径不符合预期并拒绝通过

### 与 PR 变更的关联
PR 变更仅涉及两个根级 README 文档文件（`README.md` 和 `README.en.md`），更新了可用的基础镜像 tag 列表。这些文件不是 appstore 镜像文件，不应受 appstore 路径规范约束。CI 的 appstore 规范检查器未能区分"根级文档文件变更"与"appstore 镜像目录变更"，对纯文档 PR 发出了误报。

## 修复方向

### 方向 1（置信度: 中）
此失败与 PR 代码变更本身无关，属于 CI 基础设施的规范检查逻辑缺陷——appstore 发布规范检查器未排除根级非镜像文件（如仓库根目录的 `README.md`）。修复应在 CI 工具侧（`eulerpublisher`）进行，使其只对 appstore 镜像目录下的文件进行路径校验，而非对全部变更文件一刀切地检查。

### 方向 2（置信度: 低）
若 CI 规范检查器的行为是预期设计（即要求所有 PR 的变更文件都符合 appstore 路径规范），则可能需要在仓库策略层面明确：纯文档类 PR 是否需要豁免 appstore 路径检查，或需要一个专门的 bypass 标签/机制。

## 需要进一步确认的点
1. CI 工具（`eulerpublisher/update/container/app/update.py`）中 appstore 路径检查的逻辑，确认是否设计上就对根级文件进行了路径校验，还是存在文件类型过滤的缺陷
2. 仓库是否对 appstore 路径检查有文档类变更的豁免策略
3. 同一时段内其他纯文档 PR 是否也出现相同失败（若存在则可进一步确认为 CI 工具系统性缺陷）

## 修复验证要求
无需修复——本失败属于 CI 基础设施层面的误报，不涉及 Dockerfile 或正则 patch 修改。若后续确认需要在 eulerpublisher 工具侧修改，需在 eulerpublisher 仓库中提交修复并验证根级非镜像文件的变更加不再触发 appstore 路径错误。
