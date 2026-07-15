# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包在 `dlcdn.apache.org` CDN 上返回 404，更换为 Apache 官方归档站 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 `wget` 下载源从 `https://dlcdn.apache.org/druid/...` 更换为 `https://archive.apache.org/dist/druid/...`

## 修复逻辑
分析报告指出 `dlcdn.apache.org` CDN 只保留最新版本，Druid 35.0.0 已被下架导致 HTTP 404。修复将下载源切换至 Apache 官方归档站 `archive.apache.org/dist/druid/`，该站点保留所有已发布历史版本。经 `curl -sI` 验证，`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，Content-Length: 639398150，Content-Type: application/x-gzip，确认制品可用。

## 潜在风险
同版本的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）仍使用 `dlcdn.apache.org` 源，后续重建时可能面临相同 404 失败。该文件不在本次 PR 变更范围内（`pr.changed_files` 仅含 SP4 相关文件），建议另开 PR 修复。