# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），而非 PR 变更代码导致的问题。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因是 CI 流水线中的 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）对所有 PR 无差别执行路径校验。根级 `README.md` 不在任何应用镜像目录的路径模板范围内，工具无法将其映射到有效的 appstore 发布路径，导致误判。

PR #2790 仅修改了仓库根目录下的 `README.md`，更新了可用镜像 tag 列表，不涉及任何应用镜像的 Dockerfile、meta.yml 等发布元数据文件，变更内容本身正确无误。

修复方向应在 CI 工具侧（让 `update.py` 在校验前过滤出属于应用镜像目录的变更），而非修改 PR 中的任何文件。由于 `pr.changed_files` 仅包含 `README.md`，且分析报告明确建议修复 CI 流水线配置/工具逻辑，本修复阶段不做任何代码修改。

## 潜在风险
无。未对任何文件进行修改。