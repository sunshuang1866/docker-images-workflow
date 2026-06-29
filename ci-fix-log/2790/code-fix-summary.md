# 修复摘要

## 修复的问题
CI 失败为 infra-error（基础设施问题），无需对 README 文件进行代码修改。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告明确指出该 CI 失败是 appstore 发布规范校验器（`eulerpublisher/update/container/app/update.py:273`）的路径校验逻辑与 PR 变更内容类型不匹配导致的。校验器期望变更文件路径符合 `{Category}/.../Dockerfile` 模式，而 PR #2790 仅修改了根级文档文件 `README.md` 和 `README.en.md`（更新基础镜像 Tags 列表）。根级纯文档变更不应被应用镜像上架规范校验器拦截，这是 CI 流程设计问题，根因在校验器端而非 README 文件内容。

PR 修改的 README 文件内容为合法的文档更新，无需修改。

## 潜在风险
无——当前未修改任何代码。需由 CI 维护方在校验器中增加对根级纯文档文件的豁免逻辑。