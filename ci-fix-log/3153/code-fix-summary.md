# 修复摘要

## 修复的问题
**无需代码修改**。CI 失败属于基础设施问题（infra-error）：appstore 发布规范预检工具 `update.py` 将仓库根目录的 `README.md` 纳入应用镜像路径校验范围，导致纯文档更新 PR 被误判为路径错误。

## 修改的文件
无。

## 修复逻辑
PR #3153 仅修改了根目录 `README.md`，内容是更新基础镜像可用 tags 列表的文档修正，不涉及任何应用镜像的新增或变更。`README.md` 文件内容本身是正确的，无需任何修改。

CI 失败根因在于 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑未区分应用镜像 PR 与根级文档 PR，对所有变更文件统一应用路径格式检查（期望 `/{category}/{image-name}/{version}/{os-version}/README.md` 格式），根目录 `README.md` 不匹配该模式因此被标记为 FAILURE。

实际修复需要修改 `update.py`（添加白名单过滤或放行逻辑），但该文件不在 `pr.changed_files` 允许修改的范围内（仅允许 `README.md`），因此本 PR 范围内的代码无须修改。

## 潜在风险
无。`README.md` 未做任何改动，不存在引入新问题的风险。