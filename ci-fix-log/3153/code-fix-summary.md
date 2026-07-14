# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 路径校验工具对根级文档文件（README.md、README.en.md）进行了不应有的路径格式检查，导致纯文档类 PR 被标记为 [Path Error] 失败。PR 代码变更本身正确无误，无需修改源代码。

## 修改的文件
无（infra-error，非代码缺陷）

## 修复逻辑
此为 `infra-error` 类型的 CI 失败，根因在 CI 基础架构的 `eulerpublisher/update/container/app/update.py` 中 appstore 校验工具未排除根级纯文档文件（README.md、README.en.md）。PR #3153 仅更新了 README 中可用镜像 Tags 列表的文档内容，变更完全正确。该文件不在允许修改的 `pr.changed_files` 范围内，且问题属于 CI 工具行为缺陷，不应对源代码仓库做任何修改。需要在 CI 工具侧增加根级文档文件的白名单过滤逻辑。

## 潜在风险
无