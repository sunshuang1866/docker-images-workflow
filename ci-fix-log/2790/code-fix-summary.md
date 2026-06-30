# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（基础设施问题），由 appstore 镜像发布预检工具对纯文档 PR 的误判导致。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定为 `infra-error`。仓库根目录的 `README.md` 和 `README.en.md` 不属于任何 appstore 镜像目录，不应参与镜像发布规范预检。PR #2790 仅更新了 README 中的镜像 Tags 列表，属于纯文档变更，不存在代码或构建错误。该失败应由 CI 流水线或预检工具（`eulerpublisher/update/container/app/update.py`）侧修复——为纯文档 PR 添加跳过 appstore 预检的逻辑，或在路径校验中排除非镜像目录下的文件。

## 潜在风险
无（未修改任何代码）