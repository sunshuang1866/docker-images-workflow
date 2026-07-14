# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包在 `dlcdn.apache.org` CDN 上返回 HTTP 404 导致构建失败，已将下载源切换为 Apache 归档站。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 对 Druid 35.0.0 返回 404（Apache CDN 只保留最新若干版本）。修复方案与历史 PR（#1932 phoenix、#2267 haproxy 等）一致：将下载源从 CDN 切换为 `archive.apache.org/dist/druid`，Apache 归档站保留所有历史版本。已从上游验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可访问（返回文件内容，非 404）。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史版本，不受 CDN 下架策略影响。