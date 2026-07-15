# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式11
- 新模式标题: 根级文档路径校验误报
- 新模式症状关键词: appstore specification errors, Path Error, root README.md, documentation-only PR

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI appstore 发布规范预检脚本 `update.py:273`（`eulerpublisher/update/container/app/update.py`）
- 失败原因: CI 的 appstore 发布规范检查工具对所有 PR 中修改的文件执行路径校验。该 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档更新，无任何 Dockerfile 或 meta.yml 变更）。CI 工具对根级 `README.md` 执行路径校验时，报 `[Path Error] The expected path should be /README.md`，但该文件实际就位于根路径 `/README.md`。这与模式11（PR #2512 中 `.claude/agents/README.md` 路径校验失败）症状相似，但本质不同——该 PR 中 `README.md` 的路径本身是**正确的**，校验工具给出的错误信息与实际情况矛盾，疑似 CI 工具对纯文档类 PR 的边界处理存在缺陷。

### 与 PR 变更的关联
PR #3153 的变更完全集中在 `README.md` 和 `README.en.md` 的文档内容更新（更新可用的基础镜像 tag 列表），未涉及任何镜像构建文件（Dockerfile、meta.yml、image-info.yml、image-list.yml）的新增或修改。CI 的 appstore 发布规范检查将所有变化文件纳入校验范围，对根级 `README.md` 产生了路径校验误报。此失败与 PR 的具体文档内容无关，属于 CI 工具的覆盖范围/边界条件问题。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 规范检查逻辑对根级 `README.md` 文件的路径校验处理可能存在缺陷（如路径解析相对基准目录有误、或未排除纯文档类变更）。需由 CI 维护者检查 `update.py` 中负责文件路径校验的函数（约 line 222–273 区间），排查为何根路径 `/README.md` 被判定为不符合预期路径。

### 方向 2（置信度: 低）
可能是上游 CI 工具版本与当前仓库规范存在不兼容——例如 CI 检查期望 `README.md` 仅存在于特定镜像目录下，而根级 `README.md` 被错误地纳入了 image 路径校验流程。需确认 CI 流水线触发条件是否正确排除了纯文档类 PR。

## 需要进一步确认的点
1. **获取 `eulerpublisher/update/container/app/update.py` 源码**（约 line 222–273），核实路径校验的逻辑：校验时使用的基准目录是什么，`/README.md` 如何被解析和比对。
2. **确认 CI 触发条件**：是否对纯文档 PR（无 Dockerfile/meta.yml 变更）做了正确跳过。若该 CI 检查本不应在文档 PR 上触发，则需修正 CI 流水线的触发规则。
3. **确认 PR #3153 的目录结构**是否在 CI 克隆后存在路径异常（如仓库被克隆到子目录导致根路径偏移）。
4. **对照历史案例 PR #2512（模式11）**：其中 `.claude/agents/README.md` 的路径校验错误是因为文件确实在错误位置。但本 PR 中 `README.md` 已在根路径，需确认 `update.py` 是否存在回归性缺陷。
5. 由于本次失败仅提供 x86-64 job 日志，且该 job 报错已明确指向 `README.md` 路径校验，**不需要**额外获取 aarch64 job 日志。

## 修复验证要求
本失败类型为 `infra-error`，不涉及 Dockerfile 或代码文件的修复，Code Fixer 无需执行修复操作。若 CI 维护者修复了 `update.py` 的路径校验逻辑，验证方式为：对任意纯文档类 PR（仅修改根级 README 文件）重新触发 CI，确认 appstore 检查通过。
