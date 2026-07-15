# 修复摘要

## 修复的问题
Apache Druid 35.0.0 在 CDN (`dlcdn.apache.org`) 上不可用（HTTP 404），将下载源切换为 Apache 归档站 (`archive.apache.org`)。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 builder 阶段的 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 上的 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，导致 Docker 构建在 builder 阶段失败。根因是 Apache CDN 通常只保留最新版本，历史版本可能被移除。修复方案为将下载源切换为 Apache 归档站（使用 `archive.apache.org/dist/` 路径，而非 CDN 的 `dlcdn.apache.org` 路径）。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200（Content-Length: 639398150），确认归档站上该版本可用。

## 潜在风险
SP2 Dockerfile (`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`) 仍使用 `dlcdn.apache.org` 作为下载源，存在相同的 404 风险，但该文件不在本次 PR 变更范围内，未做修改。