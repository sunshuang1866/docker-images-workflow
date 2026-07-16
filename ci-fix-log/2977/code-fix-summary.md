# 修复摘要

## 修复的问题
CI 基础设施故障：openEuler 官方软件源 `repo.openeuler.org` 在 aarch64 构建节点上发生 HTTP/2 传输不稳定，导致 `yum install` 下载包失败。与 PR 代码变更无关，无需修改任何源代码。

## 修改的文件
无。此失败为 infra-error，不需要代码修改。

## 修复逻辑
分析报告明确指出此为 infra-error（置信度: 高）：构建日志中的 `Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR` 和 `Curl error (56): SSL_ERROR_SYSCALL` 均由 openEuler 官方软件源在构建时段的瞬时传输不稳定导致。Dockerfile 中的 `RUN yum install -y` 命令语法正确，包名均有效。

推荐操作：在 openEuler 仓库服务恢复稳定后重新触发 CI 构建（Retry）。

## 潜在风险
无。