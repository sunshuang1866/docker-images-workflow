# 修复摘要

## 修复的问题
openEuler 24.03-LTS-SP4 软件仓库镜像 HTTP/2 传输层协议错误导致 dnf install 下载 RPM 包失败（Curl error 92），为 CI 基础设施问题，无需修改源代码。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告明确指出该失败为 `infra-error`，根因是 CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，遇到 HTTP/2 传输层协议错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个包反复重试后仍失败。Dockerfile 中的 `dnf install` 指令语法和包名均正确，失败与 PR 变更无关。建议重新触发 CI 构建或等待仓库镜像服务恢复后重试。

## 潜在风险
无。