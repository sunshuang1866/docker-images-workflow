# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检（`update.py`）对所有 PR 变更文件执行路径校验，期望变更文件符合镜像发布目录结构（如 `{category}/{image}/{version}/{os}/Dockerfile`）。本 PR 仅变更了 repo 根目录下的 `README.md` 和 `README.en.md` 两个纯文档文件，这些文件不属于应用镜像发布路径，被校验器误判为路径错误——要求它们位于 `/README.md` 路径下，实际上 `README.md` 本身就在该路径但依然被标记为 FAILURE，表明校验逻辑对根目录文档文件存在误判。

### 与 PR 变更的关联
PR 变更内容仅为更新 README 文档中基础镜像的可用 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，调整 latest 指向）。变更本身不涉及任何 Dockerfile、meta.yml、image-list.yml 等镜像构建文件。失败并非由 PR 代码改动的内容或质量引起，而是 CI 流水线对文档型 PR 不加区分地执行了仅适用于应用镜像 PR 的 appstore 路径校验。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线（`update.py` 的 appstore 预检逻辑）应跳过纯文档变更：当 PR 变更的文件全部位于 repo 根目录且不属于镜像目录结构（`{category}/{image}/…`）时，不应对其执行 appstore 路径校验，或应将这些文件列入白名单忽略。

### 方向 2（置信度: 中）
如果 CI 流水线不支持按文件类型跳过检查，则作为短期 workaround，可在 PR 中额外包含一个不影响镜像构建的占位变更（如对某个 `image-list.yml` 补充注释或添加/修正非关键条目），使 PR 包含至少一个通过路径校验的文件，同时 README 变更也被接受。但此方向仅为绕过方案，不解决根因。

## 需要进一步确认的点
- `update.py` 中路径校验的具体逻辑：是否存在对根目录文件的特殊处理或缺省预期路径（`/README.md`）的硬编码逻辑，导致 `README.md` 自身也被误判为 FAILURE。
- 该 CI 流水线的 appstore 预检步骤是否对所有 PR 强制执行，还是存在基于变更文件类型的条件跳过机制。
- 历史同类纯文档 PR（如 PR #2308）是否也遭遇了相同的 CI 失败，以确认这是已知的行为还是本次环境特异问题。
