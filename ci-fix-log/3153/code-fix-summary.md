# 修复摘要

## 修复的问题
CI appstore 发布规范预检（`eulerpublisher/update/container/app/update.py`）对纯文档 PR 变更文件进行路径校验时，未对无 Dockerfile 变更的纯文档 PR 做豁免处理，导致合法的 README 文档更新被错误阻断。**无需代码修改**，此为 CI 基础设施问题。

## 修改的文件
无

## 修复逻辑
分析报告明确指出根因在 CI 检查器（`update.py`）而非 PR 代码本身（"根因在 CI 检查器（非 PR 代码本身有误）"）。PR 变更了两个根目录文档文件 `README.md` 和 `README.en.md`，均为更新基础镜像可用 Tags 列表的合法文档修改，不含任何 Dockerfile 或镜像构建逻辑变更。CI 检查器未对纯文档 PR 做豁免处理，错误地将路径校验应用于非发布类变更。根据修复原则，infra-error 不应强行修改代码来绕过 CI 工具缺陷。正确修复应在 `eulerpublisher` 仓库的 `update.py` 中增加对无 Dockerfile/docker_img 变更的 PR 跳过 appstore 预检的逻辑。

## 潜在风险
无（未修改任何代码）