# 修复摘要

## 修复的问题
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org`（Apache CDN）更换为 `archive.apache.org`（Apache 官方归档站），解决 CDN 节点已下架该历史版本导致 HTTP 404 的问题。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
分析报告指出 CI 构建失败的直接原因是 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 404。Apache CDN 节点仅保留最新版本，不保证历史版本留存，Druid 35.0.0 已被下架。

修复方式与平台内模式01、02、27、38的同类 404 问题策略一致：将下载源从 CDN 迁移至 Apache 官方归档站 `archive.apache.org/dist/`，该站点保留所有历史版本。

已通过 curl 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件可正常下载。

## 潜在风险
`archive.apache.org` 若出现网络波动可能影响 CI 构建速度（历史归档站响应相对 CDN 较慢），但稳定性优于 CDN 节点的版本下架问题。无功能性风险。