# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具误将根级文档文件 `README.md` 的变更视为不合规的镜像发布路径而报 `Path Error`，导致纯文档修改的 PR 被阻塞。

## 修改的文件
无。当前 PR 仅修改了 `README.md` 的文档内容（更新可用基础镜像 tags 列表），文档内容本身没有错误，不需要修改。

## 修复逻辑
本 CI 失败属于基础设施错误（infra-error），而非代码或文档内容错误。根因是 CI appstore 预检工具 (`eulerpublisher/update/container/app/update.py`) 的路径校验逻辑未对仓库根级纯文档文件（如 `README.md`）设置白名单豁免，导致任何修改根级文档的 PR 都会被 appstore 发布规范预检拦截。该问题需要由 CI 团队在 `eulerpublisher` 工具中增加根级文档文件的白名单机制，或在 CI 流水线中调整 appstore 预检的触发条件（仅在包含镜像目录变更时触发），而非修改当前 PR 的文件内容。

## 潜在风险
无。不涉及任何代码修改，不会引入新问题。