# 修复摘要

## 修复的问题
Docker 构建时从 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包返回 HTTP 404，Apache CDN 已下架该旧版本制品。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `wget` 下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org`（Apache CDN）对 Druid 35.0.0 版本返回 404，因为 CDN 通常只保留最新版本的制品。修复方向为将下载源切换至 Apache 官方归档站 `archive.apache.org/dist/`，该站点永久保留所有历史版本。已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 且 Content-Length 为 639398150 字节，确认文件存在且可正常下载。

## 潜在风险
无