# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error）：openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在处理 HTTP/2 下载请求时对部分大型 RPM 包（`gcc-c++` 等）返回 `INTERNAL_ERROR` 帧，导致 `dnf install` 下载失败。

## 修改的文件
无。该失败与 PR #2980 引入的代码变更无关，Dockerfile 中的 `dnf install` 命令语法及包名均正确。

## 修复逻辑
分析报告确认根因为 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议层问题（`Curl error (92): Stream error in the HTTP/2 framing layer`），属于 transient infra-error。PR 新增的 Dockerfile 代码本身无任何缺陷。建议等待仓库镜像恢复后在 CI 中重新触发构建。

## 潜在风险
无