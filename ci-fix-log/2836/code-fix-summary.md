# 修复摘要

## 修复的问题
无需代码修改。CI 构建环境无法与 `archive.apache.org` 建立 TCP 443 端口连接（连接超时），属于 CI 基础设施问题（infra-error）。

## 修改的文件
无

## 修复逻辑
CI 分析报告将此失败归类为 `infra-error`。根因是 CI 构建节点与 `archive.apache.org` 之间的网络不可达，导致 Cassandra 5.0.6 二进制包下载失败（exit code 28）。此前的构建步骤（`yum install java`、`groupadd`/`useradd`）均成功，说明基础镜像和包安装正常，问题仅限于下载阶段。

需要从基础设施层面解决：
1. 排查 CI 构建节点到 `archive.apache.org` 和 `dlcdn.apache.org` 的网络连通性
2. 确认 CI 流水线中是否存在 URL 重写机制（分析报告指出 PR diff 中 URL 为 `dlcdn.apache.org`，但 CI 日志显示 `archive.apache.org`）
3. 若需更换下载源，建议使用 `dlcdn.apache.org` 或 `repo.huaweicloud.com` 等 CI 环境可达的镜像站

## 潜在风险
无（未修改任何代码）