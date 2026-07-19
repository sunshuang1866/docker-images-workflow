# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像（`repo.****.org`）在 HTTP/2 传输层出现间歇性 `INTERNAL_ERROR (err 2)` 流错误，导致 `gcc-c++`、`cmake-data`、`git-core` 等包下载失败，DNF 耗尽重试后构建终止。

## 修改的文件
无。此失败与 PR 新增的 Dockerfile 代码无关，`dnf install` 命令语法及包名均正确。

## 修复逻辑
CI 失败分析报告将失败类型归类为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 RPM 仓库镜像服务端的 HTTP/2 协议栈间歇性故障，非代码层面可修复的问题。建议在仓库镜像服务恢复正常后重新触发 CI 构建。如果重试后仍频繁出现相同错误，可考虑在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制降级到 HTTP/1.1 作为规避手段，但当前阶段无需实施代码变更。

## 潜在风险
无。未进行任何代码修改。