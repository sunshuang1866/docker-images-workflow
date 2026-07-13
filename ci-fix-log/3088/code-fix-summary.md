# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包下载源 `dlcdn.apache.org` 返回 HTTP 404，因 CDN 仅保留最新版本，35.0.0 已被移除。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/` 改为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
CI 分析报告指出 Apache CDN (`dlcdn.apache.org`) 对 Druid 35.0.0 返回 404，根因是 Apache CDN 仅保留最新版本，历史版本需从 `archive.apache.org` 获取。已将下载源切换为 `archive.apache.org/dist/druid/`，并用 `curl -I` 验证新 URL 返回 HTTP 200，确认目标文件存在。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史版本，比 CDN 更适合固定版本引用。