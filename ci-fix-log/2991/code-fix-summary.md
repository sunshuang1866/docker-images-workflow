# 修复摘要

## 修复的问题
无代码修复。CI 失败为基础设施错误（infra-error）：openEuler 官方 RPM 仓库 `repo.openeuler.org` 在 aarch64 构建期间发生 HTTP/2 流中断（Curl error 92），导致多个 RPM 包下载失败，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定为 `infra-error`，根因是 `repo.openeuler.org` 的 HTTP/2 服务端在下载时段出现瞬时连接错误（`HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），导致 `dnf install` 命令退出码为 1。PR 仅新增了标准的 vvenc Dockerfile 及配套元数据文件，Dockerfile 中 `dnf install` 命令格式正确、无语法错误。按照任务规范，`infra-error` 无需代码修改，重新触发 CI 构建即可。

## 潜在风险
无