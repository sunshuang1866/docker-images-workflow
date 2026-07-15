# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包在 `dlcdn.apache.org` 上已返回 404，原因是 Apache CDN 仅保留最新版本，历史版本会被清理。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 Druid 下载源从 `https://dlcdn.apache.org/druid/` 切换为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。Apache CDN（dlcdn）只托管各项目的最新版本，Druid 35.0.0 的 tarball 已被移除。修复方案是将下载源切换为 Apache 官方归档站 `archive.apache.org/dist/druid/`，该站点永久保留所有历史版本。已通过 WebFetch 验证该 URL 可访问（返回了 5MB+ 的 tar.gz 内容）。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站点，稳定可靠。其他版本的 Druid Dockerfile（32.0.1/sp1、34.0.0/sp1、35.0.0/sp2）目前仍使用 `dlcdn.apache.org`，若未来 CI 构建这些版本时遇到同样问题，需一并修改。