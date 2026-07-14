# 修复摘要

## 修复的问题
将 Druid 下载源从 `dlcdn.apache.org`（已下架 35.0.0 版本制品）切换为 `archive.apache.org`（Apache 官方归档站）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/...` 改为 `https://archive.apache.org/dist/druid/...`

## 修复逻辑
`dlcdn.apache.org` 只托管 Apache 各项目最新版本，Druid 35.0.0 的历史制品已从该 CDN 下架导致 HTTP 404。按照历史案例（模式01），将下载源统一回退到 `archive.apache.org`，该归档站保留所有 Apache 历史版本。已通过 `curl -sI` 验证新 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，确认制品存在且可下载。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，与 `dlcdn.apache.org` 提供相同的制品，仅分发节点不同。