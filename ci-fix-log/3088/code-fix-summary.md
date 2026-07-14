# 修复摘要

## 修复的问题
Druid 35.0.0 构建时 wget 下载返回 HTTP 404，原因是从 `dlcdn.apache.org`（CDN 实时分发节点）下载历史版本 `apache-druid-35.0.0-bin.tar.gz` 失败，该 CDN 不保留旧版本。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行，将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/...` 改为 `https://archive.apache.org/dist/druid/${VERSION}/...`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 只保留最新版本，Druid 35.0.0 已从 CDN 下架导致 404。Apache 归档站 (`archive.apache.org`) 保留所有历史发布版本，是历史版本构建的正确下载源。修复后 URL 格式为 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`，已验证该归档 URL 可正常访问并下载。

## 潜在风险
无