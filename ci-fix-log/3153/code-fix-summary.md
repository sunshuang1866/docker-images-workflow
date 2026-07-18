# 修复摘要

## 修复的问题
CI appstore 发布规范校验工具对根目录 `README.md` 路径格式报错（期望 `/README.md`，实际检测为 `README.md`）。此失败属于 CI 基础设施问题，`README.md` 内容本身无需修改。

## 修改的文件
- 无代码修改（PR 仅涉及 `README.md` 文档更新，文档内容正确无误）

## 修复逻辑
该 CI 失败由 `eulerpublisher/update/container/app/update.py` 中的路径规范化缺陷导致——`git diff` 提取的文件路径为 `README.md`（无前导 `/`），而 appstore 校验逻辑期望 `/README.md`（有前导 `/`），比对不匹配触发 PATH ERROR。同时，此 PR 仅修改仓库根级 README 文档（更新基础镜像可用 tags 列表），属于纯文档变更，不应纳入 appstore 发布规范的路径校验范畴。

由于 PR 变更文件列表仅包含 `README.md`，且 `update.py` 不在可修改范围内，此问题应在 CI 基础设施侧解决：
1. 修复 `update.py` 中 git diff 路径提取与预期路径比对的格式归一化逻辑
2. 或为仅修改根级文档文件（`*.md`）的 PR 添加跳过 appstore 校验的白名单机制

## 潜在风险
无。`README.md` 未做任何内容修改，不影响任何功能或流程。