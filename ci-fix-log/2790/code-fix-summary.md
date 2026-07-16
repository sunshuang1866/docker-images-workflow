# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范路径校验对纯文档 PR 的 `README.md` 错误触发路径校验失败。无需代码修改。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告定位的根因是：PR #2790 仅修改了仓库根目录的 `README.md` 文档（更新支持的 Tags 列表），不涉及任何应用镜像构建文件（Dockerfile、meta.yml、image-list.yml 等）。CI 的 appstore 发布规范检查器设计用于校验镜像构建 PR 中的文件路径（格式为 `{category}/{image}/{version}/{os-version}/`），却将根级文档文件 `README.md` 错误地纳入检查范围，导致路径校验失败。

这是一个 **infra-error**（CI 基础设施误报），而非代码缺陷。`README.md` 的内容变更完全合法，无需修改。正确的解决方向是由 CI pipeline 配置调整，使纯文档类变更跳过 appstore 规范校验（例如通过 PR 标签 `documentation` 或 `docs-only` 区分文档 PR 与镜像构建 PR）。

## 潜在风险
无。PR 仅涉及文档更新，不影响任何构建产物或镜像发布。