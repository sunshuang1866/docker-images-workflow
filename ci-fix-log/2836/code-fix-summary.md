# 修复摘要

## 修复的问题
Cassandra 5.0.6 在 `dlcdn.apache.org` 上已下架，下载返回 196 字节的 HTML 页面，tar 解压失败。

## 修改的文件
- `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`: 将 Cassandra 二进制包下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org`（Apache 官方归档站）

## 修复逻辑
根据 CI 分析报告，`dlcdn.apache.org` 仅保留各项目的最新版本，历史版本（Cassandra 5.0.6）已被下架，与知识库模式01（Apache CDN 404）根因一致。将下载 URL 从 `https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`，使用 Apache 官方归档站（永久保留历史版本）。已通过 `curl -sI` 验证新 URL 返回 HTTP 200，Content-Type 为 `application/x-gzip`，Content-Length 为 72645918 字节，确认为有效 gzip 包。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方的版本归档站，稳定可靠。