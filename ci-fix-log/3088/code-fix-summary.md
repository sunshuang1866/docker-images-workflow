# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包从 `dlcdn.apache.org` CDN 下载返回 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `wget` 下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，不保证历史版本 35.0.0 的持续可用性。`archive.apache.org` 是 Apache 归档站，永久保留所有历史发布版本。已通过 WebFetch 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常访问（200 OK）。

## 潜在风险
无