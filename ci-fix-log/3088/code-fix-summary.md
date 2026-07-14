# 修复摘要

## 修复的问题
Dockerfile 中 `wget` 下载 Druid 35.0.0 二进制包时，从 `dlcdn.apache.org` 下载返回 HTTP 404（Apache CDN 不再保留旧版本），已将下载源更换为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 `wget` URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 只保留最新版本，35.0.0 的二进制包已在 CDN 上被移除，导致 404。Apache 归档站 `archive.apache.org` 长期保留所有历史版本，是官方推荐的备选下载源。已通过 `curl -I` 验证修复后的 URL 返回 HTTP 200，文件存在且可访问（Content-Length: 639398150）。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期稳定可用。该 URL 与上游 Druid 官方文档中归档路径 `dist/druid/${VERSION}/` 格式一致。