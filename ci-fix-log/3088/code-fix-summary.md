# 修复摘要

## 修复的问题
Apache Druid 35.0.0 下载 URL 从 `dlcdn.apache.org` 切换为 `archive.apache.org`，解决 CDN 下架历史版本导致 HTTP 404 的问题。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行的 `wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告中指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，Druid 35.0.0 已从 CDN 下架导致 404。修复方案是将下载源切换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。此修复与历史模式 01（Maven）和模式 38（ActiveMQ）的同类问题处理方式一致。

已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 OK，文件大小约 639MB，确认归档站可用。

## 潜在风险
无