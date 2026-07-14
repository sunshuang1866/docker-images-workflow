# 修复摘要

## 修复的问题
Druid 35.0.0 下载源 `dlcdn.apache.org` 返回 404，将下载 URL 替换为 Apache 归档站 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 `wget` 的 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/...` 改为 `https://archive.apache.org/dist/druid/${VERSION}/...`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 节点，仅保留最新版本，Druid 35.0.0 二进制包已被下架导致 HTTP 404。Apache 归档站 `archive.apache.org/dist/druid/` 保留所有历史版本，是可靠替代方案。已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，与 CDN 节点的制品内容一致，仅为不同分发端点。