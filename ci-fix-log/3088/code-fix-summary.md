# 修复摘要

## 修复的问题
Dockerfile 中 wget 下载 Apache Druid 35.0.0 的 URL 使用了 `dlcdn.apache.org` CDN，该 CDN 仅保留最新版本，历史版本（35.0.0）已下架，导致 HTTP 404。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出根因是 `dlcdn.apache.org` CDN 对 Druid 35.0.0 返回 HTTP 404（该 CDN 仅保留最新版本制品）。修复方案是按分析报告"方向 1"建议，将下载源切换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。已通过网络请求验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在（返回二进制文件内容，非 404）。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站点，长期保留所有历史版本制品，比 `dlcdn.apache.org` 在此场景下更可靠。