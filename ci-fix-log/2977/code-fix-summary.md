# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 CI runner 到 `repo.openeuler.org` 的网络连接不稳定导致，与 PR #2977 的代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`，根因是 aarch64 runner `ecs-build-docker-aarch64-04-sp` 在从 `repo.openeuler.org` 下载 RPM 包时遭遇 HTTP/2 帧层错误（Curl error 92）和 SSL 读取错误（Curl error 56）。Dockerfile 结构正确，`yum install` 命令语法无误，所列 RPM 包名均有效。修复方式为重新触发 CI 构建，无需修改任何代码。

## 潜在风险
无