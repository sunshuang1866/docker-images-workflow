# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包在 `dlcdn.apache.org` CDN 上已下架（HTTP 404），导致 Docker 构建在 builder 阶段失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/` 切换为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本，旧版本下架后返回 404。Apache Archive (`archive.apache.org/dist/`) 保留所有历史版本，将下载 URL 从 CDN 切换为归档站即可解决问题。已通过 `wget --spider` 验证新 URL 返回 HTTP 200，确认 Apache Druid 35.0.0 的二进制包在归档站存在且可达。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史发行版，URL 格式稳定。