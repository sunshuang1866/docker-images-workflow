# 修复摘要

## 修复的问题
Dockerfile 中 `wget` 从 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包返回 HTTP 404，更换为 Apache 归档站地址。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载源 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，Druid 35.0.0 已下架导致 404。修复方向是将下载源更换为 Apache 归档站 `archive.apache.org`，该站保留所有历史版本。已从上游 `archive.apache.org` 获取 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 验证，返回 HTTP 200，文件存在且可达。

## 潜在风险
`archive.apache.org` 在历史 CI 环境中偶有网络不可达的情况（参考模式 33）。若构建环境中 `archive.apache.org` 不可达，可换用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（已验证返回 HTTP 200）。