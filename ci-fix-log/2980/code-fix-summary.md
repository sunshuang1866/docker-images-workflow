# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`，由 openEuler 24.03-LTS-SP4 镜像源 HTTP/2 流传输异常（Curl error 92）导致 `gcc-c++` 等 RPM 包下载失败，属于 CI 基础设施间歇性问题。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 `repo.****.org` 镜像站的 HTTP/2 协议层传输异常，与 PR 代码变更无关。PR 新增的 Dockerfile 中 `dnf install` 命令和包列表均正确无误。建议重试 CI 构建即可。

## 潜在风险
无