# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11（YAML / 元数据文件错误 — 路径校验子类）
- 新模式标题: (不适用 — 已有模式可覆盖)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）通过 `git diff` 检测到根目录 `README.md` 被修改后，将其纳入 image 级别路径格式校验，而 `README.md` 位于仓库根目录（非 `{category}/{image}/{version}/{os-version}/` 结构），不符合 appstore 镜像路径规范，校验失败。

### 与 PR 变更的关联
PR 变更仅涉及 `README.md` 和 `README.en.md` 两个文件的文档内容更新（添加新的基础镜像 tag 条目：`24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`，并将 latest 别名从 sp2 迁移到 sp4）。**PR 的文档更新本身正确无误**，失败与 PR 改动内容无关。

**根因是 CI 工具的校验逻辑缺陷**：appstore 预检工具不应将仓库根目录的 `README.md`（全局项目文档）纳入 image 层级路径规则进行校验。`README.md` 不隶属于任何镜像子目录，CI 工具将其误判为不符合路径规范的 image 级文件。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，**Code Fixer 无需修改 PR 中的任何文件**。问题需要在 CI 工具侧（`eulerpublisher/update/container/app/update.py`）修复：在收集 `git diff` 变更文件后，应过滤掉仓库根目录下的非镜像文件（如 `README.md`、`README.en.md`、`.gitignore` 等），仅对镜像目录内的文件执行 appstore 路径规范校验。这不是 PR 仓库代码范畴的问题。

### 方向 2（置信度: 低）
如果 CI 工具侧短期无法修改，可考虑将本次 PR 的变更拆分为两部分：将根 `README.md`/`README.en.md` 的文档更新单独提交为一个 PR（可能需要特殊处理或绕过 appstore 预检），将其他任何镜像级变更分开提交。但考虑到本次 PR **仅**修改了根级文档文件，拆分无实际意义——问题本质是 CI 工具误检。

## 需要进一步确认的点
1. CI appstore 预检工具（`update.py:273`）的完整校验逻辑——确认是否有白名单机制可以豁免根目录文件，以及为何当前版本未正确过滤根级文件。
2. 该 CI 预检工具在检测到只有根级文件变更时，是否应该直接跳过（返回 PASS）而非执行路径校验。

## 修复验证要求
（无需填写——本次失败为 infra-error，与 PR 代码无关，Code Fixer 不应修改任何 PR 文件。）
