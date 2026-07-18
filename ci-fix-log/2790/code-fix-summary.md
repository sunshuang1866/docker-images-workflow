# 修复摘要

## 修复的问题
无代码修改。CI 失败为基础设施错误（infra-error），根因在 `eulerpublisher` CI 工具的 appstore 路径校验逻辑缺陷，与 PR #2790 的 `README.md` 文档变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出：`eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检流程错误地将仓库根目录的纯文档文件（`README.md`）纳入 appstore 路径校验范围，且 diff 输出路径与校验期望路径之间存在前导 `/` 格式不匹配。PR #2790 仅修改了 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表），属于纯文档维护变更，未涉及任何应用镜像相关文件。

此问题需由 CI 基础设施团队修复 `eulerpublisher` 工具的校验逻辑（排除根级文档文件或修正路径格式），无需对当前 PR 仓库文件做任何修改。

## 潜在风险
无