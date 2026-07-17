# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施误报（infra-error），CI 工具 `update.py` 的应用商店路径校验逻辑将根目录 `README.md` 错误地纳入校验范围，导致文档类 PR 被阻断。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出失败根因是 `eulerpublisher/update/container/app/update.py` 中的应用商店发布规范检查工具对 PR 变更文件做路径合规校验时，未将仓库根目录的项目文档（`README.md`）从校验流程中排除。`README.md` 是项目级文档，不属于任何应用商店镜像目录结构，CI 工具不应将其纳入应用商店路径校验。

此问题必须通过修改 CI 工具（`update.py`，路径校验前的白名单过滤逻辑）来解决，属于 infra-error。PR #3153 仅修改了 `README.md` 的内容（更新可用基础镜像 tags），内容本身无问题，无法通过修改 `README.md` 绕过 CI 校验。

## 潜在风险
此判断意味着该 CI 步骤将继续阻断所有仅修改根目录文档文件（如 `README.md`、`README.en.md` 等）的 PR，需由 CI 维护团队在 `update.py` 中增加根目录文档白名单后解决。