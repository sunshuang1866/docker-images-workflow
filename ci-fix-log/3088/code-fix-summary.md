# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包下载源从 `dlcdn.apache.org` 改为 `archive.apache.org`，解决 Apache CDN 仅保留最新版本导致历史版本 404 的构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本制品。Druid 35.0.0 的二进制包已被 CDN 下架导致 HTTP 404。`archive.apache.org` 是 Apache 官方归档站点，保留所有已发布版本的历史制品。已将下载源切换至归档站点。

已从上游验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小 610MB，确认可用。

## 潜在风险
无。archive.apache.org 中的路径格式与 dlcdn.apache.org 不同（增加了 `/dist/` 前缀），已在 URL 中修正。该归档站点在 CI 环境中可正常访问。