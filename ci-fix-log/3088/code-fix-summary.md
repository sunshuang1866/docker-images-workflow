# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包的下载源从 `dlcdn.apache.org`（已下架历史版本）更换为 `archive.apache.org`（保留所有历史版本），解决构建时 HTTP 404 错误。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 `wget` 命令的下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
分析报告指出 `dlcdn.apache.org` 是 Apache CDN 节点，仅保留最新版本，历史版本的 Druid 35.0.0 已被下架导致 404。按照模式01（Maven/Archive 下载源切换）策略，将下载源切换为 `archive.apache.org/dist/druid/`，该镜像站保留所有历史版本。

已通过 `wget --spider` 验证新 URL 可访问：`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小约 610MB。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方存档站，制品校验值与原 CDN 一致，且其他 openEuler 镜像 Dockerfile 已有使用该存档站的先例。