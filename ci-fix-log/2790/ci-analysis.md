# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）在校验 PR 变更文件的路径时，对根目录下的 `README.md` 报出路径错误——校验工具期望路径为 `/README.md`（绝对路径格式），但传入或比对的路径可能为 `README.md`（相对路径格式），两者字符串不匹配导致 FAILURE。这与 PR 的内容变更无关，是 CI 工具本身的路径比对逻辑缺陷。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅修改 `README.md` 和 `README.en.md` 的内容（更新基础镜像支持的 Tags 列表：将 `24.03-lts-sp2 → 24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 独立条目）。该 CI 失败发生在 eulerpublisher appstore 发布规范的**路径校验**环节，校验的是文件路径格式是否符合规范，而非文件内容。即使 README.md 内容未做任何改动，此路径校验逻辑同样会触发失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 的 `update.py:273` 行附近，appstore 路径校验逻辑在进行路径比对时，可能存在绝对路径（`/README.md`）与相对路径（`README.md`）的字符串不匹配问题。需检查该校验函数中获取文件路径的来源（如 git diff 输出的路径格式），并统一为标准格式（如统一加或去掉前导 `/`）后再进行比对。

### 方向 2（置信度: 低）
若路径格式本身没有问题，则该路径校验规则可能对于仓库根目录下的 markdown 文档文件（非镜像 Dockerfile 相关文件）有特殊的白名单/豁免逻辑未生效，需检查校验流程中是否遗漏了对 `README.md` 这类非镜像构建文件的跳步处理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑具体实现——确认其获取文件路径的来源（git diff output、clone 后的本地路径等）以及比对规则。
2. 确认该 appstore 路径校验中对于根目录 `README.md` 是否有预期的放行逻辑，以及为何放行逻辑未生效。
3. 确认此 CI 检查是否为本次 PR 才引入的新检查项，还是一个旧的已有检查——以判断是否为 CI 工具近期变更引入的回归。
