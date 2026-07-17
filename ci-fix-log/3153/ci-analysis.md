# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

CI 差异检测日志:
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）在检测到 PR 变更了 `README.md` 后，对该文件进行路径校验，判定其"路径不符合 appstore 发布规范要求"。然而 `README.md` 位于仓库根路径 `/README.md`，是项目的主文档，并非某个 appstore 镜像目录下的 README。本 PR 为纯文档修改，未涉及任何 Docker 镜像、Dockerfile、meta.yml 或 image-info.yml 的变更，不应触发 appstore 发布规范检查。

### 与 PR 变更的关联
PR 仅修改了两个文件：
- `README.md` — 将 `24.03-lts-sp2, 24.03, latest` 修正为 `24.03-lts-sp4, 24.03, latest`（原标签指向错误的 SP1 URL），并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签条目
- `README.en.md` — 同上（英文版）

PR 不包含任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 或其他 appstore 镜像相关文件的变更。CI appstore 发布规范预检（`update.py`）将根级 `README.md` 的变更误判为需要校验的 appstore 镜像变更，从而触发路径规则校验失败。该失败并非由 PR 改动内容本身引发（改动内容正确且必要），而是 CI 对文档类 PR 的校验范围不匹配所致。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 预检工具不应将仓库根级 `README.md` 纳入镜像发布规范校验范围。根级 `README.md` 是项目通用文档，不属于任何 appstore 镜像的最小目录单元。若 CI 侧的 `update.py` 是按扩展名（`README.md`）匹配校验目标，需添加排除规则，将根路径的文件排除在 appstore 校验之外。此修复属于 CI 基础设施（`eulerpublisher` 工具）侧的调整。

### 方向 2（置信度: 中）
若 CI 工具暂时无法修改，可考虑通过 PR 提交方式规避：将纯文档修改的 PR 与任何涉及 Dockerfile/镜像变更的 PR 分开提交，避免文档类 PR 触发 appstore 校验流水线。但这只是规避方案，不能从根本上解决问题。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中 diff 检测和路径校验的实现逻辑：需要确认该工具是通过什么规则（文件扩展名、路径模式、还是 PR 标签）来决定触发 appstore 发布规范检查，以及如何判定哪些文件需要校验路径。
- CI 触发条件：文档类 PR 是否应该完全跳过该 x86-64 appstore 校验 job。

## 修复验证要求
不涉及正则 patch 外部源文件，无需额外验证步骤。
