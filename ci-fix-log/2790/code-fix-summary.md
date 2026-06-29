# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 预检流水线将根目录 README 文档文件纳入 appstore 路径校验范围，导致纯文档 PR 被错误标记为 lint-error。

## 修改的文件
无需代码修改。

## 修复逻辑
本次 CI 失败属于 **infra-error**（CI 基础设施问题）。PR #2790 仅修改了 `README.en.md` 和 `README.md` 的文档内容（更新 supported tags 列表），属于纯文档更新。失败由 CI 的 appstore 预检脚本 `eulerpublisher/update/container/app/update.py` 触发——该脚本未对仓库根层级文档文件做豁免处理，导致根目录 README 被纳入 appstore 发布路径校验。这与历史案例 PR #2512（`.claude/` 目录下 README 文件被误检）模式一致。

PR 涉及的 `README.en.md` 和 `README.md` 文件本身内容无任何问题，无需修改。真正需要修复的是 CI 预检脚本中的文件过滤逻辑，但该文件不在本次 PR 变更范围之内。

## 潜在风险
无。不涉及代码修改，PR 的 README 内容变更安全。