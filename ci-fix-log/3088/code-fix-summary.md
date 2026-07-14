# 修复摘要

## 修复的问题
将 Apache Druid 35.0.0 下载源从 `dlcdn.apache.org`（CDN 节点，不保留历史版本）更换为 `archive.apache.org`（官方归档站），解决 wget 下载时 HTTP 404 错误。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行 `wget` URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本。Druid 35.0.0 的二进制包在该 CDN 上返回 404。Apache Archive (`archive.apache.org`) 长期保留所有已发布版本，URL 格式为 `archive.apache.org/dist/druid/${VERSION}/...`。经 `curl -I` 验证，`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小约 610MB，可正常下载。

## 潜在风险
无