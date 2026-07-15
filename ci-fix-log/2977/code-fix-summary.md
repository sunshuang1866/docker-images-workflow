# 修复摘要

## 修复的问题
CI 基础设施故障：openEuler 官方软件源 `repo.openeuler.org` 在 aarch64 构建节点上出现 HTTP/2 流错误（Curl error 92/56），导致 yum 下载 RPM 包（如 gcc、kernel-headers、vim-common 等）失败。**与 PR 代码变更无关，无需代码修改。**

## 修改的文件
无代码修改。

## 修复逻辑
分析报告判定失败类型为 `infra-error`，置信度高。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 中的 `yum install` 命令格式规范、包名正确。失败完全由上游软件源网络/协议波动导致，属于临时性基础设施问题。推荐操作：重试 CI 构建。

## 潜在风险
无。此修复不涉及任何代码变更，重试构建不会引入新的风险。