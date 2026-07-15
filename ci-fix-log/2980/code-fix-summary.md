# 修复摘要

## 修复的问题
无代码修改。CI 失败为 infra-error：openEuler 仓库镜像 `repo.****.org` 在构建时发生 HTTP/2 传输层临时故障（Curl error 92: INTERNAL_ERROR），导致 gcc-c++ 等 RPM 包下载失败，`dnf install` 返回退出码 1。

## 修改的文件
无

## 修复逻辑
根据 CI Failure Analyst 分析，失败与 PR #2980 的代码变更完全无关。Dockerfile 中 `dnf install` 命令语法正确、包名完整，仓库源配置未被修改。多个不同包的 HTTP/2 stream 均报告 `INTERNAL_ERROR (err 2)`，这是镜像站服务端瞬时问题。修复方式为直接重试 CI 构建。

## 潜在风险
无