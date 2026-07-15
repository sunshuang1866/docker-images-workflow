# 修复摘要

## 修复的问题
Docker 构建时 `dlcdn.apache.org` CDN 对 Apache Druid 35.0.0 返回 404，将下载源更换为长期保留历史版本的 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出根因是 `dlcdn.apache.org` CDN 不再托管 Druid 35.0.0 版本的二进制包（HTTP 404）。Apache Archive (`archive.apache.org`) 长期保留所有历史版本，是替代下载源的合适选择。已通过 `curl -I` 验证替换后的 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方档案服务器，长期保留历史版本，不会像 CDN 节点那样下架旧版本。