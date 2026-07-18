# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发发布检查
- 新模式症状关键词: README.md, Path Error, appstore, eulerpublisher, 文档变更

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具）
- 失败原因: CI 的 `eulerpublisher` 应用商店发布校验工具（`update.py`）检测到仓库根目录的 `README.md` 发生了变更，将其作为应用镜像发布候选进行路径格式校验。由于根级 `README.md` 不属于应用镜像发布物，其路径不符合应用镜像的预期路径规范，导致校验失败。该 PR 仅包含文档类变更（`README.md` 和 `README.en.md`），本质上是 CI 工具未能正确区分"文档类 PR"与"应用镜像发布 PR"。

### 与 PR 变更的关联
**与 PR 变更内容无关。** PR 对 `README.md` 和 `README.en.md` 的修改（更新基础镜像可用 Tag 列表）是合法的文档更新操作。CI 失败源于 `eulerpublisher` 工具对所有包含文件变更的 PR 均执行应用商店发布规范校验，未能识别出纯文档变更 PR 应跳过该校验步骤。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的校验逻辑需要增加对纯文档变更 PR 的豁免判断：当 PR 中所有变更文件均位于仓库根目录且不涉及任何 `image-list.yml`、`meta.yml`、`Dockerfile` 等应用镜像相关文件时，应跳过应用商店发布规范校验步骤，直接返回通过。

### 方向 2（置信度: 低）
如果 CI 工具的设计意图确实要求校验 `README.md` 的路径格式，则需确认工具的预期路径格式规范（如是否需要绝对路径 `/README.md` 而非相对路径 `README.md`），并对工具内部路径比较逻辑进行修正。但从错误上下文推断，更可能的根因是方向 1 所述的工具误判问题。

## 需要进一步确认的点
- CI 工具 `eulerpublisher/update/container/app/update.py` 中触发路径校验的入口条件具体是什么——是否基于文件后缀（如只要包含 `.md` 就校验）还是基于目录层级。
- 该 CI 失败是此 PR 的特例还是所有纯文档 PR 都会触发——需要查看 `eulerpublisher` 的工具源码确认是否有"跳过根目录文件"的过滤逻辑。
- PR #3184（日志中提到的 `fix/3153` 分支）是否已包含针对此问题的修复尝试。
