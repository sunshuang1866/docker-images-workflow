# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 `infra-error`（基础设施问题），根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议层间歇性错误（Curl error 92），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建过程中，`dnf install` 从 `repo.****.org` 下载 RPM 包时，仓库镜像服务器多次返回 HTTP/2 流错误（涉及 `cmake-data`、`git-core`、`gcc-c++` 三个不同包），其中 `gcc-c++` 下载重试耗尽后导致构建失败。这是仓库侧的网络基础设施临时间歇性故障，非 PR 代码缺陷。Dockerfile 语法正确，无需修改。

## 潜在风险
无。建议重新触发 CI 构建流水线，等待仓库服务恢复后重试。