# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：appstore 发布规范检查器将仓库根目录 `README.md` 的文档变更误判为 appstore 镜像路径校验失败，无需修改源码。

## 修改的文件
无。PR 仅修改 `README.md` 的文档内容（更新可用镜像标签列表），内容本身正确无 bug，无需修改。

## 修复逻辑
CI 失败根因在 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑：该检查器对所有被修改的 `README.md` 文件无条件执行 appstore 镜像目录路径校验，未区分根目录文档（`/README.md`）与镜像目录内的文档（如 `{category}/{image}/{version}/{os}/README.md`）。PR #3153 仅更新根目录 `README.md` 中"可用镜像的 Tags"列表，属于仓库通用文档维护，不涉及任何镜像发布内容。

由于 `update.py` 不在本 PR 的 `changed_files` 列表中，且 `README.md` 内容无需修改，**本次无需对源码仓库做任何代码变更**。正确的修复应由 CI 维护者在 `update.py` 中添加过滤逻辑：当变更文件为根目录 `/README.md` 或 `/README.en.md` 时，跳过 appstore 发布规范检查。

## 潜在风险
无。`README.md` 的标签列表更新为纯文档变更，不影响任何镜像构建或发布流程。