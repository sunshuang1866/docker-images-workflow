# 修复摘要

## 修复的问题
CI 基础设施误触及：appstore 发布规范预检工具对仓库根目录 `README.md` 错误地执行了 appstore 路径校验，导致纯文档变更的 PR 因校验失败被阻止。此为 infra-error，无需代码修改。

## 修改的文件
无。本次 CI 失败为基础设施层面错误，不涉及源码修改。

## 修复逻辑

### 根因
CI 的 appstore 发布规范校验工具（`eulerpublisher/update/container/app/update.py`）检测到 PR 变更了 `README.md`，将其作为 appstore 上架镜像的一部分进行路径校验。但 `README.md` 位于仓库根目录，是整个仓库的说明文档，不属于任何应用镜像目录。CI 工具应区分"仓库根目录 README 变更"与"应用镜像目录内 README 变更"，对根目录 README 不执行 appstore 路径校验。

### 结论
根据分析报告，失败类型为 `infra-error`，置信度"高"。PR 变更内容为纯文档更新（镜像 Tags 列表），无 Dockerfile、meta.yml 等构建文件变更。问题根源在 CI 校验工具的逻辑，不在本仓库源码中。按照任务指令"infra-error 时无需代码修改"，不对 `README.md` 做任何改动。

## 潜在风险
无。不对源码做任何修改，不存在引入新问题的风险。