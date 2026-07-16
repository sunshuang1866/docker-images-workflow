# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为基础设施问题（infra-error），由 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议层稳定性问题导致，与 PR #2980 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 仓库镜像在下载大文件时 HTTP/2 stream 异常关闭（`INTERNAL_ERROR`），导致 `gcc-c++` 等包下载失败。Dockerfile 中的 `RUN dnf install` 命令语法和包名均正确，不存在代码级别的 bug。该问题属于临时的 CI 基础设施不稳定，无需修改任何代码文件。建议重试 CI 构建即可。

## 潜在风险
无