# 修复摘要

## 修复的问题
CI 失败为 `infra-error`，由 `eulerpublisher` 工具对根目录 `README.md` 的误校验触发，**与 PR 变更内容无关**，无需对源代码进行任何修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型: **infra-error**（CI 基础设施/工具问题）
- 根因: `eulerpublisher` 工具的 appstore 发布规范预检将仓库根目录的 `README.md` 误识别为应用镜像文件，对其执行了镜像路径校验（期望路径格式为 `{category}/{image}/{version}/{os-version}/README.md`），导致 `Path Error`。
- 修复应在 `eulerpublisher` 工具侧增加文件过滤逻辑，排除仓库根目录文档文件，而非修改本 PR 的文件内容。

本次 PR 仅修改了 `README.md` 和 `README.en.md` 的文档内容（Tags 列表更新），不涉及任何镜像构建相关的代码变更，无需也不应对该文件进行任何代码修复。

## 潜在风险
无