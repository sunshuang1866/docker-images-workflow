# 修复摘要

## 修复的问题
Apache Druid 35.0.0 下载 URL 从 `dlcdn.apache.org`（仅保留最新版本，35.0.0 已返回 404）切换至 `archive.apache.org`（保留历史版本）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 只托管当前最新版本，Apache Druid 35.0.0 已从 CDN 下架导致 wget 返回 404。根据修复方向建议，将下载源切换至 `archive.apache.org/dist/druid/`，该镜像站保留所有历史版本。已通过 `wget --spider` 验证目标 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 200 OK，确认制品可用。

## 潜在风险
无。URL 格式变更仅影响下载源，制品内容（校验和）相同，`archive.apache.org` 为 Apache 官方归档站，可靠性有保障。