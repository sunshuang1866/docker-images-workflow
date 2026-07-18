# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 openEuler 24.03-LTS-SP4 官方 RPM 仓库的 HTTP/2 服务端临时性故障（Curl error 92），与 PR 代码变更无关。

## 修改的文件
无。PR 中的 Dockerfile 语法正确、包名无误，无需修改。

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`（基础设施错误）。构建过程中，openEuler RPM 仓库服务端在处理 HTTP/2 流时返回 INTERNAL_ERROR，导致 258 个包中的 3 个下载受阻（cmake-data、git-core 重试后成功，gcc-c++ 重试两次均失败）。这是仓库侧的网络/协议层临时故障，Dockerfile 本身没有问题。待仓库恢复后重新触发 CI 重试即可通过。

## 潜在风险
无