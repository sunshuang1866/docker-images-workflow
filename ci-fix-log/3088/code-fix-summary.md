# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包从 `dlcdn.apache.org` 下载返回 HTTP 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 wget 下载源从 `https://dlcdn.apache.org/druid/` 切换为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` CDN 不保留 Druid 35.0.0 的历史版本制品，导致 wget 返回 404。按照分析报告推荐的修复方向 1，将下载源切换为 `archive.apache.org`（Apache 官方归档站），该站点托管了所有 Apache 项目的历史版本。经 HTTP HEAD 请求验证，`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 200 OK，确认制品存在且可访问。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，版本持久保留，与 CDN 不同不存在历史版本下架问题。