# 修复摘要

## 修复的问题
将 Druid 35.0.0 二进制包下载源从 `dlcdn.apache.org`（CDN 已下架，返回 404）切换为 `archive.apache.org`（归档站永久保留）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 构建在 builder 阶段因 `dlcdn.apache.org` 对 Druid 35.0.0 返回 HTTP 404 而失败（Apache CDN 只保留最新版本，历史版本会被下架）。切换到 Apache 归档站 `archive.apache.org/dist/druid/` 后，该 URL 已验证返回 HTTP 200，归档站保留所有历史版本不会被下架。此修复与 CI 分析报告方向 1（高置信度）一致。

## 潜在风险
无 — 仅修改下载源 URL，不影响镜像构建的其他环节。`archive.apache.org` 为 Apache 官方归档站，可靠性有保障。