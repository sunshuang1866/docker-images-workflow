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
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/***/x86-64/***-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）将仓库根目录的 `README.md` 误判为应用镜像的 README 文件，对其执行了镜像级路径校验。根目录 `README.md` 路径不符合镜像级 `{category}/{image}/{version}/{os-version}/README.md` 的目录结构规范，校验结果返回 `[Path Error]`。

### 与 PR 变更的关联
PR 变更内容仅涉及两个根目录文档文件（`README.md`、`README.en.md`）中基础镜像 Tags 列表的更新：将 `latest` 别名从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，并修正了原条目中 tag 名称与 URL 不一致的问题（旧条目 tag 标为 SP2 但 URL 实际指向 SP1），同时补充了 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 等新条目。

CI appstore 预检工具扫描到 `README.md` 被修改后，自动将其纳入镜像发布规范的路径校验流程。由于根目录 `README.md` 并非某个应用镜像的附属文件，其路径 `README.md` 无法匹配镜像级路径模板（如 `Cloud/nginx/1.30.0/24.03-lts-sp4/README.md`），导致校验失败。

**PR 改动本身没有代码或内容错误，失败根因是 CI 工具对根目录文件执行了不适用其上下文的校验规则。**

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具（`update.py`）在扫描 PR 变更文件时，应将根目录的 `README.md` 和 `README.en.md` 排除在镜像发布规范校验范围之外。这些文件是仓库级文档，不隶属于任何应用镜像的最小目录单元，不应参与镜像级路径格式校验。修复方式：在 `update.py` 的文件过滤逻辑中添加对根目录 README 文件的豁免判断。

### 方向 2（置信度: 中）
如果 CI 工具的设计意图是"所有通过 PR 合入的文件都必须通过 appstore 规范校验，根目录 README 也被视为可上架内容"，则需在仓库根目录下创建一个符合镜像目录规范的软链接或占位结构，使 `README.md` 的路径校验能够通过。但此方向与仓库现有目录结构设计理念冲突，不推荐。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中文件过滤/校验逻辑的具体实现：确认它是基于何种规则判定一个文件需要参与 appstore 路径校验，以及是否有针对根目录文件的豁免白名单。
- 此类问题是否为已知行为——与该 PR 无关的其他纯文档 PR 是否也会遭遇同样的 `[Path Error]` 失败。如果是，则属于 CI 工具的通用缺陷，应在 `update.py` 层面统一修复。

## 修复验证要求
（不涉及正则 patch 外部源文件，无需填写）
