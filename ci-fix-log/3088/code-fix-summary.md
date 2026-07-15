# 修复摘要

## 修复的问题
Dockerfile 中 Apache Druid 35.0.0 下载源使用了 `dlcdn.apache.org`（CDN 分发节点），该节点不保留历史版本，导致 wget 返回 HTTP 404 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第9行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
分析报告根因：`dlcdn.apache.org` 是 Apache CDN 节点，仅在 Druid 发布新版本后下架旧版本制品，导致 35.0.0 版本返回 404。修复方案是将下载源更换为 `archive.apache.org/dist/druid/`（Apache 归档站），该站点长期保留所有历史发布制品。已通过 wget spider 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件可正常下载。

## 潜在风险
无