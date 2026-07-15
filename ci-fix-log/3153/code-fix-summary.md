# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 **infra-error**（CI 基础设施问题），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`。PR #3153 仅修改了仓库根目录的 `README.md`，更新基础镜像可用 Tags 列表，属于纯文档变更。CI 的 appstore 发布规范校验工具（`eulerpublisher/update/container/app/update.py`）错误地将根目录 `README.md` 纳入 appstore 路径校验范围（期望路径格式为 `{category}/{app}/{version}/{os-version}/README.md`），而该文件并非应用镜像入口文件，不应受此校验约束。

此为 CI 工具/平台的配置问题，应在 CI 基础设施层面修复（限定校验范围为 `image-list.yml` 中注册的应用镜像目录，排除仓库根目录文档），无需对 PR 的 `README.md` 做任何代码修改。

## 潜在风险
无。PR 的 `README.md` 变更内容（更新镜像标签列表）本身是正确的文档维护操作，不涉及功能代码或构建逻辑。