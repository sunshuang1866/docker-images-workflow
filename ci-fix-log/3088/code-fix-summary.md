# 修复摘要

## 修复的问题
将 Druid 35.0.0 下载源从 `dlcdn.apache.org`（返回 HTTP 404）更换为 `archive.apache.org`（返回 HTTP 200）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 通常只保留最新版本，Druid 35.0.0 历史版本已被下架导致 404。Apache 归档站 (`archive.apache.org`) 完整保留所有历史版本，不受 CDN 下架影响。已通过 curl 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，确认归档站确实托管了该版本。

## 潜在风险
无。仅变更下载源域名和路径前缀，二进制包内容完全一致。SP2 版本的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`，不在本次修复范围内）仍在用 `dlcdn.apache.org`，未来可能遇到相同 404 问题，建议另行修复。