# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级README路径误检
- 新模式症状关键词: Path Error, expected path, appstore, README.md, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范检查工具 (`eulerpublisher`) 检测到 PR 中有 `README.md` 变更，将其作为 appstore 应用镜像的 README 文件进行路径校验。仓库根级 `README.md`（路径 `/README.md`）不符合 appstore 应用镜像 README 的预期目录层级结构（应为 `{category}/{image-name}/{version}/.../README.md` 形式），导致路径校验判定为 FAILURE。PR 仅修改了该文件中的基础镜像 tags 列表和链接 URL，属于纯文档更新，CI 工具不应将根级文档纳入 appstore 镜像路径检查范围。

### 与 PR 变更的关联
PR 的改动**未触发**该失败。PR 内容为更正 `README.md` 和 `README.en.md` 中的基础镜像可用 tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09，将 latest tag 从 sp2 更新为 sp4，并修正对应 URL），这是合理的文档维护。失败根因是 CI 工具 `eulerpublisher` 的 appstore 路径校验逻辑未排除仓库根级文档文件，任何修改根级 `README.md` 的 PR 都会触发相同的误检。该失败与 PR 代码变更内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 中的 appstore 规范检查逻辑应在执行路径校验前增加过滤条件，排除仓库根级文件（`/README.md`、`/README.en.md` 等）以及非 appstore 镜像目录下的文件。具体为修改 `update.py` 中的文件差异分析部分，在遍历变更文件时跳过路径深度不符合 appstore 镜像目录结构的条目。

### 方向 2（置信度: 低）
若 CI 工具设计上不允许跳过任何文件的路径检查，则需在仓库根级 `README.md` 中添加 appstore 豁免标记。但根级 README 是仓库整体说明文档，不应受 appstore 发布规范约束，此方向不符合项目逻辑。

## 需要进一步确认的点
- `eulerpublisher` 工具中 `update.py` 的路径校验逻辑（`line:273` 附近）是否有文件过滤机制，以及其判定 FAILURE 的具体条件
- 该 CI 检查是否曾因其他 PR 修改根级 README 而出现过相同失败（用于确认是否为已知 CI 工具已知行为）
- CI 工具是否有配置项或环境变量可控制 appstore 检查的生效范围（如仅检查 `Bigdata/`、`AI/` 等分类目录）

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败为 CI 基础设施/工具行为问题，修复方向不涉及正则 patch 第三方源文件。
