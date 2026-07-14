# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包下载 URL 指向 `dlcdn.apache.org`（CDN），该 CDN 不保留历史版本，导致 HTTP 404 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行的下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，不保证历史版本 35.0.0 的二进制包持续可用。按照报告推荐的方向 1，将下载源切换为 Apache 官方归档站 `archive.apache.org/dist/druid/`，该站永久保留所有历史版本制品。

已验证：`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可达并正常返回二进制内容（>5MB），修复后构建可正常下载。

## 潜在风险
如果 archive.apache.org 归档站出现服务中断，构建会再次失败。但这是 Apache 官方归档基础设施，可靠性高。无其他风险。