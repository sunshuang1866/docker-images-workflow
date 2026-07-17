# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: appstore检查根README路径
- 新模式症状关键词: [Path Error], expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

日志上下文中，CI 首先检测到变更差异：
```
INFO: Difference: [
    "README.md"
]
```

随后对 `README.md` 执行 appstore 发布规范校验，路径检查失败。

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 将根级仓库文档 `README.md` 纳入了 appstore 路径校验范围。该工具预期 README.md 位于应用镜像目录结构内（如 `{category}/{image}/{version}/README.md`），但 `README.md` 是仓库根级文件，其路径格式（`README.md` 而非 `{目录层级}/README.md`）不满足校验规则，导致 `[Path Error]`。

### 与 PR 变更的关联
PR 仅修改了根级 `README.md` 和 `README.en.md` 中的基础镜像可用 tags 列表（添加 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，更新 latest 指向 24.03-lts-sp4）。PR 的变更内容本身是正确的文档更新，文本逻辑无误。

CI 失败由 CI 的 appstore 校验工具将根级 README.md 误纳入校验范围所致——该工具设计用于校验应用镜像 PR（需包含 Dockerfile、meta.yml 等），不应在纯文档 PR 上触发路径格式检查。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 校验逻辑应在 `update.py` 中排除根级文件（如仓库级 `README.md`、`README.en.md`），不将其纳入路径格式校验。修改 CI 工具侧的文件过滤规则，使其仅校验位于应用镜像目录结构内的文件。

### 方向 2（置信度: 低）
若无法修改 CI 工具侧逻辑，可考虑在 PR 中避免修改根级 `README.md`（但这与 PR 目的冲突，不推荐）。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近的具体路径校验逻辑——`Difference` 列表如何生成，为何只检测到 `README.md` 而未检测到 `README.en.md`，以及路径校验规则的具体实现（是否对所有 README.md 无差别校验，还是有目录深度判断）。
2. 确认历史上同类纯文档 PR（如 #2308）是否也遇到此问题，以及当时如何处理。
3. 确认此 CI 检查是否为该 x86-64 下游构建 job 的必经步骤，是否可跳过 appstore 校验直接进入 Docker build 阶段。
