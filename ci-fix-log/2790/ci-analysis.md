# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 端的 appstore 发布规范预检工具）
- 失败原因: CI 的 appstore 发布规范预检对 PR 中改动的文件进行路径合法性校验，发现 `README.en.md` 和 `README.md` 两个根目录文档文件不符合 appstore 镜像发布的路径规范（该工具期望所有变更文件遵循 `{image-version}/{os-version}/Dockerfile` 的镜像目录层级结构）。由于本 PR 仅修改了仓库根目录的两份 README 文档，未包含任何 Docker 镜像构建文件变更，因而被预检工具判定为 "Path Error"。

### 与 PR 变更的关联
PR 变更内容完全是文档更新——在 `README.md` 和 `README.en.md` 中更新了基础镜像的 Supported Tags 表格，新增了 `24.03-lts-sp3` 和 `25.09` 版本条目并调整了 latest 标签指向。这些变更本身没有语法或逻辑错误，也没有引入任何构建文件或 Dockerfile 变更。CI 失败的直接原因是 appstore 发布规范预检步骤对**所有 PR**（包括纯文档 PR）强制执行镜像路径校验，导致与 PR 的文档变更意图不匹配。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线应对纯文档类 PR 跳过 appstore 发布规范预检步骤。具体而言，在触发 CI 的入口处根据 `pr.diff` 判断变更文件类型：若 PR 仅修改仓库根目录的 `README.md`、`README.en.md` 等非镜像目录下的文档文件，则跳过 `update.py` 中的 appstore 规范校验，直接标记为通过。

### 方向 2（置信度: 中）
如果 CI 流水线不便修改，可考虑调整 PR 的分支策略或合并流程：将纯文档变更的 PR 通过其他不触发 appstore 检查的流水线入口提交（如 GitHub Actions 的其他 workflow 分支），或使用具有跳过 CI 权限的标签/提交信息跳过该步骤。

## 需要进一步确认的点
- `update.py` 中 `line:273` 的具体校验逻辑及对根目录文件的处理分支
- CI pipeline 的 trigger 条件（`multiarch/openeuler/trigger/openeuler-docker-images`）是否支持过滤纯文档变更
- 仓库是否有文档变更免检的既定流程（如 `.github/workflows` 中的路径过滤配置）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败与第三方/上游源文件的正则匹配无关。
