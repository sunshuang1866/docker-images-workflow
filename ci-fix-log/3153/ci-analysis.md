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
2026-07-14 11:28:17,839-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具内部，非仓库源码）
- 失败原因: CI 工具的 appstore 发布规范校验模块（`eulerpublisher`）检测到 PR 修改了 `README.md`，对该文件执行 appstore 镜像路径校验时因路径格式不匹配而判定 FAILURE。该文件的路径为仓库根目录的 `/README.md`，而校验工具报错称预期路径应为 `/README.md`——两者表面上一致，报错可能是校验工具在路径解析或比较时存在格式差异（如相对路径 `README.md` 与绝对路径 `/README.md` 不同）导致误判。PR 仅包含文档变更，不涉及任何 Dockerfile 或镜像构建逻辑，因此该失败与 PR 代码质量无关。

### 与 PR 变更的关联
PR 的 diff 仅修改了两个根级文档文件（`README.md` 和 `README.en.md`），内容更新为镜像 tag 列表（增加 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，调整 latest 指向）。这些变更未涉及任何 Dockerfile、meta.yml 或 image-info.yml，不属于需要 appstore 路径校验的镜像发布单元。CI 的 `eulerpublisher` 工具将本次 PR 的唯一变更文件 `README.md` 纳入 appstore 校验流程，在校验其路径时产生误报导致流水线失败。

## 修复方向

### 方向 1（置信度: 中）
本次失败为 CI 基础设施（`eulerpublisher` 工具）的校验逻辑问题：该工具不应对根级仓库文档文件（如 `README.md`）执行 appstore 镜像路径校验。修复需在 `eulerpublisher` 工具侧进行——在校验流程中增加文件路径过滤，将仓库根目录的 `README.md` / `README.en.md` 等纯文档文件排除在 appstore 路径校验范围之外。

### 方向 2（置信度: 低）
若 CI 工具实际上要求根级 `README.md` 文件也通过 appstore 校验（即校验本身是正确的），则可能存在路径表示格式不一致的问题——校验工具内部使用的路径表示（如相对路径 `README.md` 或带工作区前缀的路径）与预期格式 `/README.md` 不匹配。此方向需要在 CI 环境中复现并调试 `eulerpublisher` 的路径比较逻辑。但从 PR 性质看，该方向可能性较低：根级 README 不应该也无需满足 appstore 镜像路径规范。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 第 273 行及相邻上下文的校验逻辑：该工具如何判定文件是否需要 appstore 校验，以及路径比较的具体实现方式。
- CI 环境中的文件路径解析方式：实际传入校验模块的 `README.md` 路径是否包含额外前缀（如工作区相对路径），导致与预期 `/README.md` 比较失败。
- 确认该仓库的 CI 策略：根级 `README.md` 变更是否本当被 appstore 校验跳过。若策略本身就要求包含根文档，则当前校验属于策略层面问题而非工具 bug。
- 提供的 CI 日志来自 x86-64 下游 job（`Finished: FAILURE`），在获取 `eulerpublisher` 源码细节前无法完全排除上游 trigger job 日志中还有其他架构 job 附带的不同错误。若此后有新的 aarch64 或其他架构 job 日志可用，应交叉验证是否存在其他独立失败。
