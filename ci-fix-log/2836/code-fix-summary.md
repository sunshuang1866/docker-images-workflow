# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施网络问题（无法连接 archive.apache.org:443）。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告将此问题归类为 `infra-error`（置信度：高）。Dockerfile 第 13 行 `curl` 命令尝试从 `archive.apache.org` 下载 Cassandra 二进制包，但 CI 构建节点无法建立到该服务器的 TCP 连接，约 134 秒后超时（curl exit code 28）。该问题与 PR 代码内容无关，属于 CI 构建环境的网络不可达问题，需由 CI 运维侧排查网络出口、DNS 解析或代理配置。无需对 Dockerfile 或任何 PR 变更文件进行代码修改。

## 潜在风险
无