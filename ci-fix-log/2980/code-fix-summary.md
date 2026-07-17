# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 openEuler 24.03-LTS-SP4 上游软件仓库镜像站的 HTTP/2 传输层网络瞬态故障（Curl error 92: Stream error in the HTTP/2 framing layer），属于 CI 基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告认定该失败为 infra-error，置信度高。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 仓库中存在的合法包名。多个 RPM 包下载时遭遇 HTTP/2 流传输异常，其中 gcc-c++ 在所有镜像源均重试失败。该问题属于上游仓库镜像站的网络瞬态故障，建议重新触发 CI 构建即可，无需修改任何代码。

## 潜在风险
无