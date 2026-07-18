# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, /README.md, appstore specification

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI appstore 规范预检阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 的 appstore 发布规范预检工具对仓库根目录 `README.md` 报告路径错误，声称"期望路径应为 `/README.md`"，但该文件实际已位于仓库根路径 `/README.md`。PR 仅修改了 `README.en.md` 和 `README.md` 中 Tags 表格的内容（新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目，更新 latest 指向 SP3），未增删任何文件，也未改变文件路径结构。此错误高度疑似 CI 工具在路径比对时因前导斜杠缺失/冗余导致字符串不匹配，属于 CI 基础设施问题。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的 diff 仅涉及根目录下两个 README 文件内容的行级修改（增删若干 Tags 表格行），不涉及文件路径变更、新增文件或路径层次结构调整。CI appstore 预检工具的路径校验逻辑对根目录 README.md 产生了误报。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，无需修改 PR 代码。应由 CI 维护团队排查 `eulerpublisher/update/container/app/update.py` 中 appstore 规范预检的路径比对逻辑，确认是否存在前导 `/` 的字符串匹配缺陷。

### 方向 2（置信度: 低）
若 CI 工具无 bug，则需确认该仓库的 appstore 发布规范是否对 `README.md` 有特殊的路径约定（如要求位于某子目录而非根目录）。但从项目规范看，`README.md` 位于根目录是符合仓库目录结构的。

## 需要进一步确认的点
- CI 工具 `eulerpublisher` 中 `update.py:273` 附近的路径校验逻辑具体实现，确认是否对根目录文件路径存在前导 `/` 处理不一致
- 历史上同类仓库的 PR 是否也曾因修改根目录 README.md 触发相同的 appstore 路径校验失败
- 该仓库在 appstore 的配置中是否对 README.md 路径有特殊约定

## 修复验证要求
无需修复验证（infra-error，非代码问题）。若 CI 维护方确认工具无 bug 且确需按规范调整，code-fixer 无需操作。
