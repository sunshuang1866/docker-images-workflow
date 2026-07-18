# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（部分类似 模式11）
- 新模式标题: CI根路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: CI 预检工具 `update.py` 对仓库根目录下的 `README.md` 执行 appstore 发布规范路径校验时，无法正确处理根层级文件，产出了 `[Path Error] The expected path should be /README.md` 的误报。实际上 `README.md` 确实位于仓库根路径 `/README.md`，不存在路径错误。该 CI 工具的路径校验逻辑仅适用于 Docker 镜像子目录结构（如 `AI/...`、`Bigdata/...` 等），对根级 README 文件的处理存在缺陷。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个仓库根目录文件，内容为更新 openEuler 基础镜像的可用 Tags 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等条目）。变更是纯文档更新，内容正确且符合 README 格式规范。CI 失败并非由变更内容引起，而是 CI 预检工具在看到 PR 中仅包含根级 README 文件变更（无任何 Docker 镜像文件变更）时，路径校验逻辑产生了误报。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `update.py` 的 appstore 发布规范校验逻辑需要增加对仓库根级文件（如 `README.md`、`README.en.md`）的豁免/跳过处理。当 PR 仅涉及根级文档文件变更、不涉及任何 Docker 镜像目录时，应跳过 appstore 发布规范的路径校验。此为 CI 基础设施侧（`eulerpublisher` 工具）的修复，不应对 PR 代码做任何修改。

### 方向 2（置信度: 低）
若 CI 工具不能被修改，则可能需要确认该 PR 是否确实不应该单独提交 README 文档变更——例如 README 的 Tags 更新是否需要伴随实际的 Dockerfile/镜像变更才能通过 appstore 校验。但基于 `[Path Error]` 的错误描述，这更倾向是工具路径校验的 bug 而非业务规则限制。

## 需要进一步确认的点
- 读取 `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑，确认其对仓库根级文件的处理分支是否缺失
- 确认 openEuler 容器镜像仓的 appstore 发布规范是否允许纯 README 文档 PR（不包含 Docker 镜像文件变更）通过 CI 检查
- 对比历史 PR #2512 中类似 `.claude/README.md` 路径校验失败案件的最终修复方式（是修改文件路径还是调整 CI 工具逻辑），判断本案件应采用相同策略还是不同策略
