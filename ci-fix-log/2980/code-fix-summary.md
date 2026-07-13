# 修复摘要

## 修复的问题
CI 基础设施中的 openEuler 24.03-LTS-SP4 软件源 HTTP/2 连接瞬时故障，与 PR 代码变更无关。**无需修改任何代码。**

## 修改的文件
无。该失败为 `infra-error`，不是代码问题。

## 修复逻辑
CI 分析报告明确指出：失败类型为 `infra-error`，根因是构建环境中 `repo.****.org` 镜像站的 HTTP/2 流错误（Curl error 92），导致 `gcc-c++` 等 RPM 包下载失败。Dockerfile 语法正确、`dnf install` 依赖声明完整，与 PR 变更无直接关系。多个包（`cmake-data`、`git-core`、`gcc-c++`）均遭遇同类 Curl 92 错误，其中 `git-core` 重试后成功，说明这是临时网络/服务端抖动。建议重新触发 CI 构建，等待镜像站恢复后即可通过。

## 潜在风险
无（未修改任何代码）。