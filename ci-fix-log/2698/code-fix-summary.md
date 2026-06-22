# 修复摘要

## 修复的问题
CI 预检脚本 `parse_image_prefix` 在处理变更文件 `Database/percona/README.md` 时，因 `Database/image-list.yml` 中缺少 `percona: percona` 条目而抛出 ValueError。此失败属于 infra-error，根因在 CI 基础设施脚本，不在 PR 代码本身。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`，根因位于 CI 预检脚本 `eulerpublisher/update/container/app/format.py:156` 的 `parse_image_prefix` 函数。该函数要求所有变更文件都能在 `Database/image-list.yml` 中找到对应的镜像根目录条目。PR 新增了 `Database/percona/` 目录下的所有文件，但 `Database/image-list.yml` 中缺少 `percona: percona` 条目（该文件不在本次 PR 的变更文件列表中）。按照任务指令中"infra-error 无需代码修改"的原则，不对 PR 源代码做任何改动。实际修复需要在 `Database/image-list.yml` 末尾追加 `percona: percona`，但这超出了当前允许修改的文件范围。

## 潜在风险
若其他 PR 新增数据库镜像但遗漏更新 `Database/image-list.yml`，会触发相同的 CI 预检失败。建议在 PR 提交流程或 CI 检查中添加对 `image-list.yml` 更新的校验。