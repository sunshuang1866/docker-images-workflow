# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR触发appstore路径校验
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范检查脚本（`update.py`）对 PR 中修改的根目录 `README.md` 进行了路径校验。该检查期望变更文件落在 Docker 镜像目录（如 `Bigdata/`、`AI/` 等分类路径）下，并遵循 `{image}/{version}/{os-version}/Dockerfile` 这类发布路径格式。根目录 `README.md` 无法匹配到任何有效的镜像发布路径模式，被判定为 FAILURE。

### 与 PR 变更的关联
PR 仅修改了两个根目录文件：`README.md` 和 `README.en.md`（更新基础镜像的 Tags 列表，添加 24.03-lts-sp3 和 25.09 条目）。这是一次纯文档更新，不涉及任何 Docker 镜像的新增或版本变更（无 Dockerfile、meta.yml、image-list.yml 等镜像文件变更）。然而 CI 的 appstore 发布规范检查 job 仍被触发，将该 PR 作为镜像发布 PR 进行路径校验，导致失败。**该失败由 PR 变更触发，但 PR 变更内容本身（文档更新）是有效的。**

## 修复方向

### 方向 1（置信度: 中）
调整 CI pipeline/trigger 的调度逻辑，使纯文档 PR（仅修改仓库根目录 `.md` 文件、不涉及 Docker 镜像目录）不触发 appstore 发布规范检查 job。检查触发条件配置，增加文件路径过滤，排除仅变更 `README.md`、`README.en.md` 等仓库级文档的 PR。

### 方向 2（置信度: 低）
修改 `eulerpublisher/update/container/app/update.py:273` 附近的路径校验逻辑，使仓库根目录的文档文件（如 `README.md`、`README.en.md`）被排除在 appstore 发布文件的路径校验范围之外，或在检测到无 Docker 镜像文件变更时直接跳过检查并返回成功。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 line 273 附近的具体校验逻辑是什么？需阅读源码以确认"Path Error — The expected path should be /README.md"的真实含义以及为何根目录 README.md 被纳入检查。
2. CI pipeline 的 trigger 配置中，appstore 检查 job 的触发条件是否对变更文件类型有过滤？目前看该 job 在纯文档 PR 上也被触发。
3. 仓库规范是否允许仅修改根目录 README 文档的 PR 通过 CI？该 PR 的意图明确且内容正确，CI 应允许其合并。
