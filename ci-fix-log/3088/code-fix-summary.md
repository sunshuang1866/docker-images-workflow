# 修复摘要

## 修复的问题
Druid 35.0.0 Dockerfile 中使用 `dlcdn.apache.org` CDN 下载二进制包返回 404，已将下载源切换为 Apache 归档站 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出根因为 Apache CDN (`dlcdn.apache.org`) 仅保留最新版本，Druid 35.0.0 历史版本已被下架导致 HTTP 404。修复采用分析报告建议的方向 1：将下载源切换为 `archive.apache.org/dist/druid/`（Apache 官方归档站，永久保留所有历史版本）。已从上游获取 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 验证，HTTP 200 且文件存在（Content-Length: 639398150 bytes），确认路径和文件名匹配。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，路径格式与 `dlcdn.apache.org` 的制品结构一致（`${VERSION}/apache-druid-${VERSION}-bin.tar.gz`），仅根域名和 `/dist/` 前缀不同。