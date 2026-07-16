# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`，根因是 `repo.openeuler.org` 软件源在 aarch64 架构下 HTTP/2 流传输层不稳定（curl error 92: INTERNAL_ERROR / curl error 56: SSL_ERROR_SYSCALL），导致 `yum install` 下载 RPM 包时连接中断，属于远程服务器端或中间网络设备的临时性故障，与 PR 代码变更无关。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
分析报告确认失败与 PR 变更无关——Dockerfile 中的 `yum install` 命令写法与仓库内其他同类 Dockerfile 完全一致。失败源于 CI 构建节点从 `repo.openeuler.org` 下载 173 个 aarch64 RPM 包（总计 148 MB）时，HTTP/2 连接层间歇性故障。此问题在 openEuler 软件源恢复正常后重试 CI 即可通过，无需代码层面的修复。

## 潜在风险
无