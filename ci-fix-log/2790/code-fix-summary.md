# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：appstore 发布规范校验工具对纯文档 PR 的根级 `README.md` 执行了不合理的路径校验。

## 修改的文件
无。`README.md` 内容正确，无需改动。

## 修复逻辑
本次 PR 仅更新了项目根级 `README.md` 的基础镜像 Tags 列表（文档内容更新），不涉及任何应用镜像构建文件。CI 流程中的 `eulerpublisher/update/container/app/update.py` 将 `README.md` 识别为变更文件后，按 appstore 发布规范要求其路径必须位于 `{场景}/{镜像名}/{版本}/{系统版本}/` 目录结构下，根级文档显然不满足此条件，导致校验失败。

根级 `README.md` 属于项目整体文档，不在 appstore 应用镜像发布规范的管辖范围内。CI 触发条件过于宽泛（所有 PR 均触发 appstore 校验），应配置 CI 使纯文档 PR 跳过该检查，或使用项目已有的 CI skip 机制。

该问题无法通过修改 `pr.changed_files` 内的任何文件（仅 `README.md`）来解决，需由 CI 配置层面处理。

## 潜在风险
无。未对代码做任何修改。