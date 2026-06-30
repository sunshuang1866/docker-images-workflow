# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error）：PR #2790 仅修改仓库根级文档文件（README.md、README.en.md），不涉及任何镜像构建文件，但 CI 流水线的 appstore 路径校验脚本错误地将文档类 PR 纳入镜像发布规范校验，导致误报路径错误。

## 修改的文件
无。PR 变更的文件（README.md、README.en.md）内容正确，无需修改。

## 修复逻辑
分析报告指出根因在 `eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑，需在该脚本中增加对纯文档类 PR（仅涉及根级 README、LICENSE 等文件，不含 Dockerfile/meta.yml 等镜像文件）的过滤/跳过逻辑。该文件不在本 PR 的 `changed_files` 范围内，且属于 CI 基础设施配置范畴，不应在本次代码修复中处理。

## 潜在风险
无。PR 本身的文档变更正确，跳过本次修复不会引入任何风险。实际修复需由 CI 流水线维护方在 `update.py` 中增加文档变更过滤逻辑，或从 trigger 层排除文档 PR 的架构构建 job。