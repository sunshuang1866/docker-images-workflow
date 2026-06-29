# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `README.md`、`README.en.md`（仓库根目录）
- 失败原因: CI 的 appstore 发布规范预检（`eulerpublisher/update/container/app/update.py`）对 PR 中所有变更文件执行路径校验，仓库根目录下的 `README.md` 和 `README.en.md` 不属于任何应用镜像目录结构，不符合 appstore 发布规范的路径要求，被判定为 `[Path Error]`。

### 与 PR 变更的关联
**直接关联**。PR 对 `README.md` 和 `README.en.md` 的修改（更新镜像 Tags 列表和对应的链接 URL）触发了 CI 的 appstore 路径校验。CI 预检阶段 (`update.py:line:356`) 识别出这两个文件有变更，随后在 appstore 发布规范检查阶段（`update.py:line:273`）发现它们不满足应用镜像发布所需的目录路径格式，判定失败。

## 修复方向

### 方向 1（置信度: 高）
CI 预检工具的 appstore 路径校验规则过于宽泛，对仓库根目录下的纯文档文件（如 README.md、README.en.md、CONTRIBUTING.md 等）也执行了镜像路径校验。应在 `eulerpublisher/update/container/app/update.py` 的路径检查逻辑中，将不属于应用镜像目录结构（即不在 `Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`、`Base/` 等目录下的文件）排除出 appstore 发布规范校验范围。

### 方向 2（置信度: 低）
PR 内容本身无问题，属于纯文档更新。如果 CI 工具的校验逻辑短期内无法修改，可考虑通过 CI 配置跳过此 PR 的 appstore 发布规范检查（如通过 label 白名单机制标记纯文档类 PR）。

## 需要进一步确认的点
- CI appstore 校验代码 `eulerpublisher/update/container/app/update.py` 中路径校验的具体实现逻辑，确认其是否已有文件类型/路径过滤机制。
- 该 CI pipeline 是否对根目录文档文件变更存在白名单或跳过机制（如通过 PR label 控制）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用 — 此问题为 CI 配置/代码问题，不涉及正则 patch 外部源文件）
