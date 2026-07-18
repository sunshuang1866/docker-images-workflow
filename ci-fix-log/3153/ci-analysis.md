# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 Appstore 发布规范预检工具（`eulerpublisher`）对所有 PR 中被修改的文件执行路径合法性校验。本次 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），检测工具将 `README.md` 识别为变更文件后，发现它不符合任何应用镜像的最小目录路径模式（`{image-version}/{os-version}/Dockerfile`），因此报 `[Path Error]`。该检查设计用于应用镜像发布 PR，不应拦截仅修改根级文档的 PR。

### 与 PR 变更的关联
- PR 变更内容：更新 `README.md` 和 `README.en.md` 中基础镜像的可用 Tags 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，`latest` 标签从 sp2 迁移到 sp4）。
- 变更本身**完全正确**，不涉及任何代码、Dockerfile 或 `image-list.yml` 的修改。
- CI 失败与 PR 改动内容无关，是 CI 流水线未区分文档类 PR 与应用镜像 PR 导致的不合理拦截。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施配置问题，建议**关闭（Close）此 CI 检查结果并人工合并 PR**。PR 仅包含根级 README 文档更新，无需通过 Appstore 发布规范检查。如果有 CI 流水线配置权限，可为 `docs:` 前缀的 PR 添加跳过 Appstore 检查的规则。

### 方向 2（置信度: 低）
若 CI 流水线无法跳过该检查，可尝试在 PR 中追加一个空的、符合应用镜像路径规则的占位文件（如某个 image 目录下新增一个空 `README.md`），使 CI 检测到至少一个符合规范的镜像变更路径，从而绕过校验。**不推荐此方向**，因为会引入无意义的文件变更。

## 需要进一步确认的点
- CI 流水线（Jenkins multibranch pipeline）是否已有机型用于辨别文档类 PR（如以 `docs:` 开头）并跳过 Appstore 检查；若有但未生效，需排查 CI 配置。

## 修复验证要求
（无需验证——此失败为 infra-error，PR 代码无需修改。）
