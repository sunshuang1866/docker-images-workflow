# 修复摘要

## 修复的问题
Druid 35.0.0 构建时 wget 下载返回 HTTP 404，因为 `dlcdn.apache.org` 是 Apache CDN 分发节点，只托管最新版本，35.0.0 已从 CDN 下架。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 wget 下载源从 `https://dlcdn.apache.org/druid/${VERSION}/` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/`

## 修复逻辑
Apache Archive (`archive.apache.org`) 会永久保留所有历史版本的二进制制品，路径结构与原 CDN 一致，只需将域名和路径前缀从 `dlcdn.apache.org/druid/` 改为 `archive.apache.org/dist/druid/`。已通过 `curl -sI` 验证新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。

## 潜在风险
无。Archive 是 Apache 官方长期归档站点，永久保留历史版本，稳定性高于 CDN。