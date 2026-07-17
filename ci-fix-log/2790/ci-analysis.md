# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具在比对变更文件路径时，发现 `README.md`（git diff 产出的路径格式，不带前导 `/`）与期望的规范路径 `/README.md`（带前导 `/`）不匹配，判定为路径校验失败。

### 与 PR 变更的关联
本 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档变更，更新了支持的 Tags 列表），没有任何 Dockerfile、构建脚本或代码改动。CI 的 appstore 发布规范预检工具检测到 `README.md` 被修改，在路径比对时因前导 `/` 格式差异产生误报。此失败与 PR 文档内容无关，属于 CI 预检工具对根目录文件的路径格式处理问题。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `eulerpublisher/update/container/app/update.py` 在获取 git diff 变更文件列表时，输出的路径未添加前导 `/`（如 `README.md`），而 appstore 发布规范校验期使用带前导 `/` 的规范路径（如 `/README.md`）做比对。需在 update.py 中统一路径格式（例如在生成 diff 列表时为每个路径添加前导 `/`），使根目录文件和子目录文件的路径比对逻辑一致。

### 方向 2（置信度: 低）
若该 CI Job（`x86-64/openeuler-docker-images`）实际只负责统一检查，而 root README 本就不应触发 appstore 发布规范校验，则可能需要在 update.py 的变更检测逻辑中将根级文件（`README.md`、`README.en.md` 等）排除在 appstore 发布规范检查范围之外。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中获取 git diff 变更列表的具体实现（第 356 行附近及路径比对逻辑），确认是否因 `os.path.relpath` / `os.path.abspath` 等路径处理导致前导 `/` 不一致。
2. 确认 appstore 发布规范预检是否预期对仓库根目录的 `README.md` 进行路径校验——如果根 README 本就不属于 appstore 镜像发布范畴，则属于预检规则缺陷而非路径格式问题。
3. 确认同一仓库其他 PR 修改根目录文件是否也会触发同类路径校验失败（若不会，说明此 PR 可能存在其他未发现的差异）。

## 修复验证要求
若修复方向一涉及的 `update.py` 属于 CI 编排工具仓库（非本 PR 仓库），code-fixer 需确认该文件的修改权限和发布流程；若修改仅涉及本仓库，则需在本地复现 `update.py` 的路径比对逻辑，验证统一添加前导 `/` 后 `README.md` 能通过校验。
