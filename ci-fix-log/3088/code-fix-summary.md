# 修复摘要

## 修复的问题
Apache Druid 35.0.0 从 `dlcdn.apache.org` CDN 下载返回 HTTP 404，因 Apache CDN 不保留历史版本制品。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行下载源从 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 通常只保留最新版本制品，Druid 35.0.0 的历史版本已被下架，导致 `wget` 返回 404。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史发行版。此修复与 CI 分析报告中模式01/模式38 的解决思路一致。已用 `curl -I` 验证目标 URL 返回 HTTP 200，确认归档站确实托管了该版本二进制包。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档基础设施，稳定性有保障。URL 格式与 CDN 格式仅域名部分不同，路径结构一致。