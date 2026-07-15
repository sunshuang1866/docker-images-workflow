# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：appstore 发布规范预检工具对纯文档 PR 的 `README.md` 进行了不必要的路径校验并误报 `[Path Error]`。`README.md` 实际位于仓库根目录（即 `/README.md`），路径合法，错误为 CI 工具的误报。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定失败类型为 `infra-error`，根因是 CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对纯文档类变更的文件执行了不适用于文档文件的路径校验。PR #3153 仅更新了 `README.md` 中的基础镜像可用 tags 列表，未涉及任何 Dockerfile、meta.yml 或镜像构建文件。根据修复原则，infra-error 应定位为 CI 基础设施/工具问题，不应通过修改 PR 代码来解决。

应由 CI 团队调整 `update.py` 中的文件过滤逻辑，使 appstore 预检仅对镜像目录内的文件（如 Dockerfile、meta.yml、image-info.yml）执行校验，忽略根目录纯文档文件。

## 潜在风险
无。未对源码做任何修改。