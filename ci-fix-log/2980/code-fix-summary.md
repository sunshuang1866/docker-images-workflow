# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议流错误（Curl error 92: INTERNAL_ERROR）导致 RPM 包下载失败，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时遭遇 HTTP/2 服务端流错误，两次重试均失败。Dockerfile 语法正确，所列包名均为标准包。该失败属于临时性基础设施/网络问题，应在 CI 中重新触发构建（如回复 `/retest`）解决。

## 潜在风险
无