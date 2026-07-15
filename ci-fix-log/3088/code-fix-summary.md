# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包从 `dlcdn.apache.org` CDN 下载返回 HTTP 404，切换为 `archive.apache.org` 归档站。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，不保证历史版本可用。35.0.0 版本在该 CDN 上已不可达（返回 404）。将下载源切换为 `archive.apache.org`（Apache 归档站，保留历史版本）。已通过 `curl -I` 验证新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。

## 潜在风险
无。同一个 35.0.0 版本的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）仍使用 `dlcdn.apache.org`，该构建可能同样面临 404 问题，但不属于本次 PR 的变更文件范围。