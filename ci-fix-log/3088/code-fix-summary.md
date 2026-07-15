# 修复摘要

## 修复的问题
Apache Druid 35.0.0 下载源 `dlcdn.apache.org` 返回 HTTP 404，导致 Docker 构建 `wget` 失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 `wget` 的下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，35.0.0 已返回 404。`archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是 Apache 官方归档站，保留所有已发布版本。已通过 `curl -sI` 验证新 URL 返回 HTTP 200 (Content-Length: 639398150)，确认制品可下载。

## 潜在风险
无。归档 URL 是 Apache 官方维护的持久化存储，不会移除已发布版本。