# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包在 `dlcdn.apache.org` 上返回 HTTP 404，导致 Docker 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 wget 下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发节点，通常仅保留最新版本，不保证历史版本持久可用。将下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（Apache 归档站，保留所有历史版本）。已验证 archive URL 可访问（HTTP 200），Apache Druid 35.0.0 制品确实存在于归档站。

## 潜在风险
无。archive.apache.org 是 Apache 官方归档站，所有历史版本均可获取。该修复与项目中其他同类问题的处理方式一致（模式01、模式33、模式38）。