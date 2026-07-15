# 修复摘要

## 修复的问题
将 Druid 35.0.0 二进制包的下载源从 `dlcdn.apache.org`（已返回 404）替换为 `archive.apache.org`（Apache 官方归档站，永久保留历史版本）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行，wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` CDN 已下架 Druid 35.0.0 的二进制包，导致构建时 wget 返回 HTTP 404。根因是该 CDN 仅保留最新版本，历史版本会被清理。修复方案采用 Apache 官方归档站 `archive.apache.org/dist/druid/`，该归档站永久保留所有历史版本。

已从 `archive.apache.org` 验证 `apache-druid-35.0.0-bin.tar.gz` 确实存在且可下载（HTTP 200, Content-Length: 639398150 bytes），URL 可达确认无误。

## 潜在风险
无。仅更换了下载域名，URL 路径、文件名和版本号均未变更，不影响镜像内容的一致性。