# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具（`update.py`）对 PR 变更的两个 README 文件进行路径校验，均未通过。`README.en.md` 的期望路径为 `/README.md`但文件名为 `README.en.md`（不匹配）；`README.md` 也已同样理由被标记为失败，但其失败具体原因在日志中无法完全确认。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中可用基础镜像 tags 的行（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，调整 24.03-lts-sp2 的链接 URL）。由于这两个文件是 PR 中唯一的变更，CI 的 appstore 规范检查器自动检测到差异文件列表即为 `["README.en.md", "README.md"]`，进而对二者执行路径校验并双双报错。PR 对 README 内容的修改本身不引入路径问题，但触发了 CI 的路径规约检查。

## 修复方向

### 方向 1（置信度: 高 — 针对 README.en.md）
`README.en.md` 的路径错误是明确的：CI appstore 检查器期望所有 README 类型文件统一使用 `README.md` 命名，不支持 `.en.md` 这种语言后缀变体。修复方向是调整 `README.en.md` 的命名或修改 CI 检查器的路径匹配规则（如允许 `README.*.md` 通配），使其不再被标记为 Path Error。

### 方向 2（置信度: 低 — 针对 README.md）
`README.md` 位于仓库根目录（即 `/README.md`），路径本身与检查器期望值 `"/README.md"` 一致却仍报错，原因不明。可能的情况包括：
- CI 检查器在处理 PR 差量上下文时存在路径解析缺陷（如将工作树路径与仓库根路径混淆）；
- 检查器对 `README.md` 有额外的内容格式校验（如必含特定元数据/表头字段），但错误信息被统一归类为 "Path Error"；
- 检查器在克隆 PR 分支后，实际存在的 `README.md` 路径因某种原因与期望不匹配（如子模块、符号链接等）。

需要进一步确认后决定修复策略。

## 需要进一步确认的点
1. **`README.md` 失败的真实原因**：日志中 `README.md` 已处于 `/README.md` 位置却仍报 Path Error，此矛盾点需要在 CI 源码（`eulerpublisher/update/container/app/update.py:222-273`）中排查，确认检查逻辑是用何种方式对比路径（绝对路径 vs 相对路径、是否包含仓库根前缀、是否受工作目录影响）。
2. **CI appstore 规范对 README 文件的确切要求**：需查阅 appstore 发布规范文档，确认是否允许 `README.en.md` 这类后缀变体存在，以及英文 README 的正确放置和命名方式。
3. **该检查是否为本次 PR 触发的已知问题**：检查是否有其他仅修改 `README.en.md` 的 PR 也以同样方式失败了，以判断是否为 CI 检查器本身的问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用（本次失败不涉及对外部源文件的正则 patch 操作）。
