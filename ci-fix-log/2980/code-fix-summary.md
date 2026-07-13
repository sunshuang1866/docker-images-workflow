# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），openEuler 24.03-LTS-SP4 镜像站在构建期间出现 HTTP/2 流错误（Curl error 92），导致 `gcc-c++` 等 RPM 包下载失败。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出该失败类型为 `infra-error`，根因是上游 openEuler 24.03-LTS-SP4 RPM 仓库镜像的 HTTP/2 协议层临时不稳定，与 PR #2980 的代码变更无关。Dockerfile 中的 `dnf install` 命令语法正确、包名合法。此类错误属于 transient 网络故障，无需修改源代码，直接重试 CI 构建即可通过。

## 潜在风险
无