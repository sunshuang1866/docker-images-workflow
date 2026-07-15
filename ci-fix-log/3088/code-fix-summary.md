# 修复摘要

## 修复的问题
Docker 构建时从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0 返回 HTTP 404，将下载源切换为 Apache 归档站 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行将 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，历史版本（如 Druid 35.0.0）会被下架，导致 HTTP 404。`archive.apache.org` 是 Apache 官方归档站，保留所有历史版本，是 CI 构建下载历史版本的可靠来源。此修复与知识库中模式01（Maven）和模式38（ActiveMQ）的同类问题处理方式一致。

已通过 `curl -sI` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小 639MB，确认该归档 URL 有效。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档基础设施，稳定性高。使用 `${VERSION}` 变量传递版本号，未来升级版本只需修改 ARG VERSION 参数即可。