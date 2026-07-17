# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）—— appstore 发布规范预检工具将根目录 `README.md` 误判为镜像发布候选文件，导致 Path Error。PR 内容本身无问题，无需修改源代码。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败分析报告指出：根因位于 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检逻辑。该工具将 PR 所有变更文件均视为 appstore 发布候选，根目录 `README.md` 不属于任何镜像发布路径（`{Category}/{Image}/{Version}/Dockerfile`），因此路径校验失败。

然而 `eulerpublisher/update/container/app/update.py` 不在 PR 变更文件列表（`['README.md']`）中，且分析报告确认"失败并非由 PR 内容错误引起，而是预检规则对文档类变更过于严格"。根据修复规范，此类 `infra-error` 无需修改源代码，应由 CI 团队修复预检工具的过滤逻辑——在 `eulerpublisher/update/container/app/update.py` 中增加根目录非镜像文件（如 `README.md`、`CONTRIBUTING.md` 等）的跳过条件，使其不被当作 appstore 发布候选。

## 潜在风险
无——源代码未做任何修改，PR 变更的 `README.md` 内容合法合规。