# 修复摘要

## 修复的问题
ActiveMQ 6.1.7 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 下载 URL 返回 HTTP 404，构建失败。

## 修改的文件
- `Others/activemq/6.1.7/24.03-lts-sp4/Dockerfile:28`: 将 ActiveMQ 下载源从 `dlcdn.apache.org//activemq` 更换为 `archive.apache.org/dist/activemq`，同时修正了原 URL 中的双斜杠拼写错误。

## 修复逻辑
分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，只保留最新版本，不保证历史版本（如 6.1.7）的可用性，导致 wget 返回 404。修复方案将下载源更换为 `archive.apache.org`（Apache 官方归档站），该站点永久保留所有历史版本。

已通过 `wget --spider` 验证新 URL `https://archive.apache.org/dist/activemq/6.1.7/apache-activemq-6.1.7-bin.tar.gz` 返回 HTTP 200，确认可达。

## 潜在风险
无。同日期的 SP1/SP2 版本 Dockerfile 使用相同的 `dlcdn.apache.org` 源，可能也有同样的潜在问题，但不在本次 PR 修改范围内，如需一并修复需另提 PR。