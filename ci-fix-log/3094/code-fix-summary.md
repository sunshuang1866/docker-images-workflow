# 修复摘要

## 修复的问题
HBase 2.6.5 下载源 `dlcdn.apache.org` 返回 HTTP 404，导致 Docker 构建失败。

## 修改的文件
- `Bigdata/hbase/2.6.5/24.03-lts-sp4/Dockerfile`: 将 curl 下载 URL 从 `https://dlcdn.apache.org/hbase/${VERSION}/hbase-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/hbase/${VERSION}/hbase-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本制品，HBase 2.6.5 已被移除导致 404。Apache Archive (`archive.apache.org`) 永久保留所有历史版本。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/hbase/2.6.5/hbase-2.6.5-bin.tar.gz` 返回 HTTP 200，确认归档站可用。

## 潜在风险
无。同一镜像的其他版本（SP3）也使用同一 CDN 下载源，可能存在相同的潜在风险，但按最小化原则不在此次修复中修改。

## 验证结果
已用 `curl -sI` 验证 `archive.apache.org/dist/hbase/2.6.5/hbase-2.6.5-bin.tar.gz` 返回 HTTP 200。