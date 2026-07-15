# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR触发应用商店校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 应用商店发布规范校验工具）
- 失败原因: PR 仅修改了仓库根目录下的文档文件（`README.md`、`README.en.md`），CI 流水线中的 `eulerpublisher` 应用商店发布规范校验工具检测到 `README.md` 变更后，将其纳入应用商店发布规范检查流程。根目录的 `README.md` 不符合应用商店镜像条目路径规范（`{category}/{image}/{version}/{os-version}/`），导致路径校验失败。

### 与 PR 变更的关联
PR 变更仅修改了 `README.md` 和 `README.en.md` 中的受支持镜像 Tags 列表（新增 25.09、24.03-lts-sp3、24.03-lts-sp2 条目，更新 latest 指向），变更内容本身是正确的文档更新，不涉及任何应用商店镜像条目的新增或修改。CI 失败是由 CI 流水线将文档类 PR 错误地路由至应用商店发布规范校验 job 所致，与 PR 的代码变更质量无关。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线配置层面修复：为应用商店发布规范校验 job 添加变更文件类型过滤，排除仓库根目录下的纯文档文件（`README.md`、`README.en.md` 等），使文档类 PR 不触发应用商店规范检查。此类 PR 应仅触发基础 CI 检查（如 markdown lint），而非应用商店发布校验。

### 方向 2（置信度: 低）
若该 CI 行为是设计意图（即要求所有 PR 都通过应用商店路径校验），则需在 `eulerpublisher` 校验规则中添加根目录 `README.md` 的豁免逻辑，或在项目规范中明确文档类 PR 的提交约束。

## 需要进一步确认的点
1. 该 CI 应用商店发布规范校验 job 是否有配置化的文件类型过滤机制（如 `.ci/paths-filter.yml` 或 Jenkinsfile 中的 `when.changes` 指令），以确认修复应落在 CI 流水线层面还是 `eulerpublisher` 工具代码层面。
2. 过往类似的纯文档 PR（仅修改根目录 README）在该仓库中是否也遇到过同类 CI 失败，抑或本次是 CI 流水线配置变更后首次触发。
3. 确认 `eulerpublisher/update/container/app/update.py:273` 处的校验逻辑是否应区分"应用商店镜像条目变更"和"仓库文档变更"两类场景。
