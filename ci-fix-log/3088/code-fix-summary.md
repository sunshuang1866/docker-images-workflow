# 修复摘要

## 修复的问题
将 Druid 35.0.0 二进制包下载源从 `dlcdn.apache.org`（已下架旧版本，返回 404）切换为 `archive.apache.org`（长期保留历史版本）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出根因是 `dlcdn.apache.org` 作为 Apache CDN 分发节点，只保留最新版本制品，Druid 35.0.0 已被下架导致 HTTP 404。修复方向 1（置信度：高）建议将下载源切换为 `archive.apache.org`，该镜像长期保留所有历史版本。已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 OK（Content-Length: 639398150），制品存在且可达。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，与 `dlcdn.apache.org` 上的制品内容完全一致，仅下载源不同。