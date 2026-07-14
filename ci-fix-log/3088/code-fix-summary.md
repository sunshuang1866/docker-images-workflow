# 修复摘要

## 修复的问题
Docker 构建时从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0 二进制包返回 404 Not Found，已将下载源替换为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 替换为 `wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` CDN 仅托管 Apache 项目的最新版本，Druid 35.0.0 已从 CDN 下架。替换为 `archive.apache.org`（Apache 归档站），该站保留所有历史版本。已从上游 `https://archive.apache.org/dist/druid/35.0.0/` 验证，`apache-druid-35.0.0-bin.tar.gz` 文件确实存在（610M，2025-10-27），文件名格式与 Dockerfile 中的 `${VERSION}` 变量构造一致。

## 潜在风险
无。仅修改下载源 URL，不改变构建逻辑、文件路径或版本号。