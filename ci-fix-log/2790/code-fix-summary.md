# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具误将仓库根目录下的 `README.md` 纳入镜像发布路径校验，导致纯文档变更 PR 被错误标记为 Path Error。

## 修改的文件
无代码修改。`pr.changed_files` 仅包含 `README.md`，该文件内容本身没有问题；CI 失败根因在 CI 基础设施（`eulerpublisher/update/container/app/update.py`），不在 PR 变更范围内。

## 修复逻辑
本次 CI 失败属于 **infra-error**（CI 基础设施问题）：
- 根因：CI 流水线对 PR 统一执行 appstore 发布规范预检，但未将仓库根目录下的 `README.md`、`README.en.md` 等非镜像发布文件纳入白名单/跳过列表。
- 修复方向：需要在 `eulerpublisher/update/container/app/update.py` 的 `Difference` 过滤逻辑中增加对根级文档文件的跳过处理，或调整 CI 流水线触发条件以允许纯文档变更 PR。
- 该修复需要由 CI 维护者操作，不属于本次 PR 代码变更范围。

## 潜在风险
无 —— `README.md` 未被修改，不存在代码层面风险。CI 基础设施修复后，后续类似纯文档 PR 可正常通过检查。