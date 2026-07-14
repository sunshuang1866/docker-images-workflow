# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包下载 URL 从 `dlcdn.apache.org` 更换为 `archive.apache.org`，修复 HTTP 404 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` CDN 上不存在 Druid 35.0.0 的二进制包（返回 404），而 `archive.apache.org` 归档站保留了历史版本。已通过 `curl -sI` 验证新 URL 返回 HTTP 200，包可正常下载。这与 CI 分析报告中方向 1（置信度: 高）的修复建议一致。

## 潜在风险
无。仅更换了下载源域名和路径，包内容完全一致（均为同一版本 `apache-druid-35.0.0-bin.tar.gz`）。