# 修复摘要

## 修复的问题
CI 构建失败是由 openEuler 24.03-LTS-SP4 软件仓库的临时性 HTTP/2 服务端故障（Curl error 92: Stream error in the HTTP/2 framing layer）导致，与 PR 代码变更无关，无需代码修复。

## 修改的文件
无

## 修复逻辑
分析报告确认为 `infra-error`：构建过程中 `dnf install` 从 `repo.****.org/openEuler-24.03-LTS-SP4/` 下载 RPM 包时，HTTP/2 协议层发生 `INTERNAL_ERROR`，导致 `gcc-c++` 等包下载失败。这是 openEuler 仓库服务端的临时问题，PR 新增的 Dockerfile 及元数据文件均无错误。建议重试 CI 构建，无需修改任何代码。

## 潜在风险
无