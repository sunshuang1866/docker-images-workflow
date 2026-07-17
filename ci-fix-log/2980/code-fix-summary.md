# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因是 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 流层间歇性错误（Curl error 92），导致 `gcc-c++` 等 RPM 包下载失败，属于 CI 基础设施层的瞬时网络故障，与 PR 代码变更无关。

## 修改的文件
无。

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`，根因是 `repo.****.org` 镜像站的 HTTP/2 服务端不稳定，导致 `dnf install` 步骤中部分 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）反复遇到 `HTTP/2 stream ... was not closed cleanly: INTERNAL_ERROR` 错误。其中 `gcc-c++` 在所有镜像重试后仍无法下载，构建失败。Dockerfile 中的 `RUN dnf install -y ...` 命令在语法和逻辑上无问题。重新触发 CI 构建（方向 1）是推荐方案。**不应对代码做任何修改。**

## 潜在风险
无。