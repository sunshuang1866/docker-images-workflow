# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（基础设施问题）：CI 的 appstore 预检工具 (`eulerpublisher/update/container/app/update.py`) 对纯文档 PR 错误地执行了镜像路径校验，将根级 `README.md` 误判为路径不符。

## 修改的文件
无。`README.md` 内容正确，不存在需要修复的代码问题。

## 修复逻辑
- 本 PR (#3153) 仅修改了仓库根目录下的 `README.md`，属于纯文档变更，未涉及任何 Dockerfile 或镜像构建文件。
- CI 失败的直接原因是 `update.py:273` 处的 appstore 路径校验逻辑要求变更文件位于 `{category}/{image}/...` 路径结构下，而根级 `README.md` 不符合该模式。
- 这是一个 CI 预检工具的缺陷：该工具未对纯文档 PR（不含镜像目录变更）进行豁免处理。
- 修复此问题需要修改 CI 工具 `eulerpublisher/update/container/app/update.py`，但该文件不在本 PR 的变更文件列表 (`pr.changed_files`) 中，且属于 CI 基础设施代码，不应在源码仓中修改。

## 潜在风险
无。`README.md` 无需任何改动，该 CI 失败可通过在 CI 工具链中增加对根级文档文件的过滤逻辑来解决，或由 CI 管理员手动跳过纯文档 PR 的 appstore 预检。