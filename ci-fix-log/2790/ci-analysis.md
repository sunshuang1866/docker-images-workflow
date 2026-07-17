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
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了仓库根目录下的 `README.md` 和 `README.en.md`。该工具期望变更文件遵循容器镜像发布目录结构（`Category/Image/Version/...`），根目录 `README.md` 不属于任何镜像发布路径，预检工具的路径校验无法将其映射到合法的发布路径规范，报 Path Error 并导致 CI 失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件（更新基础镜像 Tags 列表：将 `24.03-lts-sp2, 24.03, latest` 修正为指向 `SP3` 路径，并新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 的独立条目）。这些文件是仓库的主文档，不包含任何容器镜像构建定义。CI 预检工具将 PR 的所有文件变更均视为 appstore 发布候选，根目录 README 无法通过发布路径规范校验，因此失败并非由 PR 内容错误引起，而是预检规则对文档类变更过于严格。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具应排除仓库根目录文档文件（`README.md`、`README.en.md`、`CONTRIBUTING.md` 等）的路径校验，使其不被当作 appstore 镜像发布候选进行检查。修改点可能在 `eulerpublisher/update/container/app/update.py` 中 `Difference` 检测后的过滤逻辑处，需增加根目录非镜像文件的跳过条件——例如检查变更文件是否位于已知的场景分类目录（`Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Others/`）下，若否则直接跳过发布规范校验。

### 方向 2（置信度: 低）
若 CI 策略规定不允许通过 PR 直接修改根目录 README，则此 PR 需通过其他渠道（如 maintainer 直接推送到 master）完成文档更新，CI 侧无需修改。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——是否硬编码了只接受特定目录结构（如 `{category}/{image}/{version}/Dockerfile`）的文件变更，以及根目录文件被拦截的具体代码位置
2. 该仓库的 CI/appstore 发布策略是否明确禁止通过 PR 修改根目录 `README.md`，或 CI 工具的行为属于 bug
3. 若方向 2 成立（策略禁止），当前仓库的根 README 维护流程是什么

## 修复验证要求
若修复方向为调整 CI 预检过滤逻辑，code-fixer 需在修改 `eulerpublisher` 工具后，验证：(1) 根目录 `README.md` 修改不再触发 Path Error；(2) 正常镜像目录（如 `Bigdata/spark/4.1.2/24.03-lts-sp4/Dockerfile`）的文件变更仍能正常通过 appstore 发布规范校验，不会被误跳过。
