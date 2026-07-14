# 修复摘要

## 修复的问题
CI 基础设施/网络问题（`infra-error`），无需修改 PR 代码。构建失败根因为 openEuler 24.03-LTS-SP4 仓库镜像服务器 HTTP/2 连接不稳定，导致大文件 RPM 包（如 gcc-c++ 13 MB）反复下载失败。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确判定失败类型为 `infra-error`，置信度为高。失败原因是 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时遇到 HTTP/2 流层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），与 PR 新增的 Dockerfile 代码变更无关。PR 中新 Dockerfile 的包名声明均合法正确。建议重试 CI 构建（日志中同批次 cmake-data 和 git-core 重试后成功，表明该错误为间歇性网络问题）。

## 潜在风险
无。未对代码做任何修改。