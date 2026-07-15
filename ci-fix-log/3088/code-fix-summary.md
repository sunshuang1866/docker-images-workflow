# 修复摘要

## 修复的问题
Druid 35.0.0 下载 URL `dlcdn.apache.org` CDN 返回 HTTP 404，将下载源更换为 Apache 归档站。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行，将下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，不保证历史版本的长期可用性，Druid 35.0.0 的二进制包已在该 CDN 上被移除。修复方向是将下载源切换至 Apache 归档站 `archive.apache.org`，该站点会长期保留历史版本。已验证新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，归档站上存在该版本包。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史发布版本，不会像 CDN 一样移除旧版本。