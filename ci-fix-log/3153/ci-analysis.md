# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 校验工具内部）
- 失败原因: CI 的 appstore 发布规范预检将仓库根目录 `README.md` 的变更视为 appstore 条目进行路径校验，要求其遵循镜像目录的路径格式规范（如 `{category}/{image}/{version}/{os-version}/README.md`），但根目录 `README.md` 是仓库级文档，不适用该规范，导致 `[Path Error]` 校验失败。

### 与 PR 变更的关联
PR 仅修改 `README.md` 和 `README.en.md` 的文档内容（更新可用基础镜像 tag 列表，新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 等条目），未新增任何镜像目录、Dockerfile 或元数据文件。CI 失败由 appstore 路径校验工具对根目录文档文件的校验逻辑触发，与 PR 文档变更的实质内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 校验工具（`update.py`）需将仓库根目录文档文件（`README.md`、`README.en.md` 等）加入路径校验豁免列表，不应要求根目录文档遵循镜像子目录的路径格式规范。此修复需由 CI 维护方在 `eulerpublisher` 工具侧完成，PR 作者无需修改代码。

## 需要进一步确认的点
- 确认 CI 校验工具 `eulerpublisher` 当前是否已对根目录 `README.md` / `README.en.md` 设置了路径豁免逻辑，以及为何该豁免未生效
- 参考 模式11 中 PR #2512 的同类案例（`.claude/README.md` / `.claude/agents/README.md` 触发 appstore 路径校验失败），确认是否为同一 CI 校验工具的问题复现

## 修复验证要求
无需填写（infra-error，根因在 CI 校验工具侧，不涉及 PR 代码修复）。
