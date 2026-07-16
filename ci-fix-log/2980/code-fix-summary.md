# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 openEuler 24.03-LTS-SP4 仓库镜像的临时 HTTP/2 流错误导致。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，置信度高。根因是 openEuler 24.03-LTS-SP4 RPM 仓库镜像（`repo.****.org`）在 CI 构建期间出现间歇性 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` 等部分 RPM 包下载失败。该问题与 PR 代码变更无关，Dockerfile 中 `dnf install` 命令语法正确。修复方向应为重新触发 CI 构建（re-run），而非修改代码。

## 潜在风险
无。