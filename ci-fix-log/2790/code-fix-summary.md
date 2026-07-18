# 修复摘要

## 修复的问题
CI 基础设施问题：appstore 规范校验工具 (`eulerpublisher/update/container/app/update.py`) 对所有 PR 无条件执行，纯文档类 PR（仅修改仓库根目录 `README.md`）无法通过面向镜像发布的路径校验逻辑，导致误报 `[Path Error]`。

## 修改的文件
无代码修改。

## 修复逻辑
本 PR (#2790) 仅修改了仓库根目录的 `README.md`（更新基础镜像 Tags 列表中的 URL 和新增版本条目），属于纯文档更新，不涉及任何 Dockerfile 或镜像元数据文件。CI 失败的直接原因是 CI 流水线中的 appstore 规范校验 job 无条件对所有 PR 执行，而 `README.md` 位于仓库根路径，不在任何镜像子目录下，无法通过面向镜像发布的路径校验。

此问题的根因在 CI 基础设施层面（Jenkins pipeline / CI 编排配置），而非 PR 所修改的源代码。根据约束规则，`README.md` 本身无需且无法通过代码修改来解决此 CI 失败。正确的修复方向是在 CI 编排层面增加文件类型判断逻辑——当 PR diff 仅包含仓库根目录文档文件且不包含任何镜像目录下的 `Dockerfile`/`meta.yml` 时，跳过 appstore 校验步骤。

## 潜在风险
无。本摘要未对源代码做任何修改，不影响已有功能。