# 修复摘要

## 修复的问题
Druid 35.0.0 构建时从 `dlcdn.apache.org` 下载二进制包返回 HTTP 404，因为 Apache CDN 只托管最新版本。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载源从 `dlcdn.apache.org/druid/` 改为 `archive.apache.org/dist/druid/`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，Druid 35.0.0 已从 CDN 下架。将下载源切换为 `archive.apache.org/dist/druid/`（Apache 归档站，保留所有历史版本），与知识库中模式01和模式38的修复策略一致。已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，归档源可达。

## 潜在风险
无。归档站 `archive.apache.org` 是 Apache 官方历史版本归档次，与 CDN 不同，会长期保留所有已发布版本。