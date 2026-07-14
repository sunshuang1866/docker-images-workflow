# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 变更了 `README.en.md` 和 `README.md` 两个根目录文件，并将它们视为 appstore 上架项进行路径校验。这两个文件不在 appstore 镜像上架所需的目录结构规范内（该规范期望的路径为镜像目录结构如 `/{category}/{image}/{version}/Dockerfile`），因此路径校验失败。

### 与 PR 变更的关联
PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 两个纯文档文件（更新基础镜像可用 tags 列表），未涉及任何 Dockerfile、镜像配置或元数据文件。CI 的 appstore 预检工具对所有变更文件强制进行路径规范校验，文档文件被误判为不合规的上架项。**该失败并非 PR 代码变更的错误，而是 CI 检查工具对文档类变更兼容性不足所致。**

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具应排除纯文档文件（如仓库根目录下的 `README.md`、`README.en.md`）的路径校验，避免对非镜像上架相关文件的变更报错。可在 `update.py` 的差异检测逻辑中，增加对根目录 README 文件的白名单过滤，将 `README.md` 和 `README.en.md` 排除在上架规范检查范围之外。

### 方向 2（置信度: 中）
若 CI 检查工具不支持白名单机制，可考虑将本次 PR 的文档变更剥离，单独通过免检通道提交（如带有特定 label 的 PR 跳过 appstore 预检），或要求 CI 工作流在触发 appstore 预检前先判断变更文件类型——若所有变更文件均不属于镜像目录结构，则跳过该检查。

## 需要进一步确认的点
- `update.py` 中差异检测和路径校验的具体逻辑，确认是否已有文件白名单机制或可扩展点
- CI 工作流层面是否有条件跳过 appstore 预检的机制（如基于 changed files 类型判断）
- 历史类似案例（如模式11 中的 `.claude/agents/README.md` 路径校验失败）的最终修复方案，以确定团队对此类问题的处理惯例

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次失败不涉及对外部上游源文件的正则修改。）
