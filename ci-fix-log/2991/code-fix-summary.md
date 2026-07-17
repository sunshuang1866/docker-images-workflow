# 修复摘要

## 修复的问题
CI 基础设施问题，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败类型为 **infra-error**，失败原因是 openEuler 官方仓库（`repo.openeuler.org`）在 aarch64 架构的 Docker 构建过程中出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），属于下游仓库服务端的临时性故障，与 PR 变更无关。Dockerfile 中的 `dnf install` 命令语法正确，包名有效，无需修改任何代码。建议重新触发 CI 构建即可。

## 潜在风险
无