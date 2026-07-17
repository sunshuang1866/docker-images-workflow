# 修复摘要

## 修复的问题
CI appstore 发布规范检查工具对纯文档 PR 产生误报，`README.md` 被错误判定为路径校验失败。此失败为 **infra-error**，无需对源码仓库进行任何代码修改。

## 修改的文件
无代码修改。

## 修复逻辑
PR #3153 仅修改了 `README.md`（和 `README.en.md`），更新了基础镜像可用 Tags 列表的文档内容，属于纯文档类变更，不涉及任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 等镜像构建相关文件。CI 的 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）对纯文档变更 PR 不适用，产生了误报。根据分析报告结论（方向 1，置信度: 高），此错误属于 CI 基础设施问题，应由 CI 管理员在触发/调度层增加过滤逻辑，当 PR 仅变更仓库根目录的文档文件且不含镜像构建文件时跳过 appstore 规范校验步骤。本 PR 的源码无需任何修改。

## 潜在风险
无。不涉及代码修改。