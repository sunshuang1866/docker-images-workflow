# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包从 `dlcdn.apache.org` 下载返回 HTTP 404，因为该 CDN 不保留历史版本制品。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` 仅托管最新版本制品，Druid 35.0.0 已下架导致 404。`archive.apache.org` 保留所有历史 release 制品，可正常访问。已通过 `curl -I` 验证目标 URL（`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）返回 HTTP 200。

## 潜在风险
无