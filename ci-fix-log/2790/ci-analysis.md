# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发CI校验
- 新模式症状关键词: Path Error, expected path, appstore, specification errors, README.md, update.py

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273` (CI appstore 发布规范校验)
- 失败原因: PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档变更），但触发了 CI 的 appstore 镜像发布规范校验流水线。校验工具检测到 diff 中存在 `README.md`，该文件位于仓库根路径 `/README.md`，不属于任何有效的 appstore 镜像目录路径（如 `AI/{image}/`、`Bigdata/{image}/` 等），导致路径校验直接报 `FAILURE`。

### 与 PR 变更的关联
PR 的改动（更新 README.md 和 README.en.md 中支持的镜像 Tags 列表——添加 24.03-lts-sp3、25.09，同时修正 latest 标签从 sp2→sp3）直接触发了此次 CI 失败。这不是代码/构建层面的错误，而是纯文档类 PR 被 appstore 发布校验流水线拦截——该流水线本应用于验证镜像 Dockerfile 提交的路径合规性，对根目录纯文档变更不应生效。

## 修复方向

### 方向 1（置信度: 中）
**CI 流水线层面：增加 PR 变更文件路径过滤。** 在触发/编排 job（`multiarch/openeuler/trigger/openeuler-docker-images`）中增加逻辑：仅当 PR diff 包含有效镜像目录路径下的文件（如匹配 `{场景分类}/{镜像名}/{版本}/{os版本}/` 结构）时才触发 appstore 发布校验。根目录纯文档变更应直接跳过该检查或标记为通过。

### 方向 2（置信度: 低）
**在 `update.py` 校验逻辑中增加根目录文件的豁免规则。** 在 `update.py:273` 附近的校验逻辑中，对仅修改根目录文件（如 README.md、README.en.md）的 PR 直接放行，因为这些文件不属于任何镜像发布条目，不应当受 appstore 路径规范约束。

## 需要进一步确认的点
1. CI 触发层的 job 配置是否支持按文件路径过滤 PR 触发条件（需要查看 `multiarch/openeuler/trigger/openeuler-docker-images` 的 Jenkinsfile 或流水线配置）
2. `eulerpublisher/update/container/app/update.py:273` 的校验逻辑中，`README.md` 被检测到的具体证据（为何 `README.en.md` 未被列出，差异检测逻辑是否配置了白名单）
3. 该 CI 流水线是否为该仓库所有 PR 的必经检查（即是否每个 PR 都会触发 appstore 校验），或者是因为 PR 带有特定标签/触发条件才被路由到该 job
4. 上游项目中是否存在针对"纯文档 PR 被 CI 拦截"的已有豁免策略

## 修复验证要求
本问题属于 CI 流水线/校验工具逻辑层面，与 Dockerfile 构建或上游源码无关。修复方向涉及 CI 配置或 `eulerpublisher` 工具的校验规则调整，非代码编译/测试问题，无法直接通过重新触发构建来验证。需由 CI 维护方确认流水线触发策略后进行调整，建议先在非生产环境验证"仅修改根目录文档文件的 PR 不再触发 appstore 校验"。
