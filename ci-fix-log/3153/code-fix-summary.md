# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（基础设施误报），是 CI 工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检对纯文档 PR 的路径校验误判。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了 README.md 文档内容（更新基础镜像可用 Tags 列表），未涉及任何应用镜像 Dockerfile 或元数据文件。CI 的 appstore 发布规范预检将 `README.md`（相对路径）与 `/README.md`（绝对路径）判定为不匹配，属于 CI 工具层面的误报，与 PR 实际代码变更无关。此类 infra-error 应在 CI 工具侧修复（例如按 PR 变更文件类型跳过 appstore 规范检查，或在路径比较逻辑中做归一化处理），不应在源码仓库中做改动。

## 潜在风险
无