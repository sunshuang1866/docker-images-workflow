# 修复摘要

## 修复的问题
Dockerfile 中 Apache Druid 下载 URL 使用 `dlcdn.apache.org` CDN 导致 404 错误，已将下载源切换为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` CDN 不保留 Apache Druid 35.0.0 的历史版本制品，导致 HTTP 404。修复将下载源切换到 Apache 官方归档站 `archive.apache.org/dist/druid/`，该站点保留所有历史版本。已通过 `wget --spider` 验证新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，确认可达。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，稳定托管所有历史版本的制品，且 URL 格式与现有项目中的其他类似修复一致。