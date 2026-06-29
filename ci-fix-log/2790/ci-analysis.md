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
2026-06-29 15:21:41,552-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `update.py:273`（CI appstore 发布规范校验逻辑）
- 失败原因: CI 的 appstore 发布规范检查 (`update.py`) 识别到 PR 修改了根目录下的 `README.en.md` 和 `README.md`，这两个文件路径不符合 appstore 镜像发布所期望的目录结构（如 `{category}/{app-name}/{version}/{os-version}/...`），触发路径校验失败。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的 `README.en.md` 和 `README.md` 两个文档文件（更新镜像 Tags 列表及对应 URL）。这些是纯文档修改，不涉及任何 Dockerfile 或应用镜像的变更。CI 的 appstore 发布规范检查被触发后，因根目录文件不属于任何预期的 appstore 镜像路径模式而报错。**该失败与 PR 的代码变更内容无关，属于 CI 校验逻辑不够完备的问题**——它未区分"文档类根目录文件修改"和"应用镜像文件修改"。

## 修复方向

### 方向 1（置信度: 中）
PR 本身是纯文档更新，无需修改 PR 内容。问题在于 CI 流水线的 appstore 发布规范检查未对根目录文档文件（`README.md`、`README.en.md`）做豁免处理。应在 CI 检查逻辑中增加判断：对于 PR diff 中仅包含根目录文档文件的情况，跳过 appstore 路径校验，或将其视为合规放行。

### 方向 2（置信度: 低）
如果 CI 要求所有 PR 都必须通过 appstore 发布规范检查且不允许豁免，则需检查 `update.py` 中的路径校验逻辑，确认其对根目录 README 文件的处理是否存在缺陷（例如将 `README.en.md` 也纳入了镜像发布路径校验范围）。

## 需要进一步确认的点
1. CI appstore 发布规范检查 (`update.py`) 的完整路径校验逻辑：它究竟如何判断文件路径是否符合规范？对根目录 README 文件是否有特殊处理逻辑？
2. 该 CI 检查是否应该对所有 PR 执行——对于纯文档修改 PR（不涉及任何应用镜像），是否应该跳过此检查？
3. 对比历史成功合并的纯 README 修改 PR，确认它们是否也触发过相同检查以及结果如何。

## 修复验证要求
（不适用——PR 内容本身无需修改，问题在于 CI 校验逻辑对根目录文档文件的处理方式。）
