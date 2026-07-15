# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error 类型，系 `eulerpublisher` 工具对根级文档文件 `README.md` 不恰当地执行了 appstore 发布规范路径校验所致，属于 CI 基础设施误报。

## 修改的文件
无。PR 仅包含 `README.md` 的文档内容更新（基础镜像 Tag 表格），变更本身不涉及任何 Dockerfile、构建脚本或镜像目录，不存在需要修复的代码问题。

## 修复逻辑
分析报告明确判定本次失败为 infra-error（置信度：中）。CI 工具 `eulerpublisher` 对仓库根级文档 `README.md` 执行了本不应触发的 appstore 路径校验，错误提示"expected path should be /README.md"与实际路径一致却仍报 FAILURE，进一步指示 CI 工具可能存在路径比对逻辑缺陷。此类问题需在 CI 编排层面修复（如增加根级文档白名单），代码层面无需且不应做任何修改。

## 潜在风险
无。不对 PR 代码做任何修改，不影响原有功能。