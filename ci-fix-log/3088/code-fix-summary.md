# 修复摘要

## 修复的问题
Druid 35.0.0 Docker 镜像构建失败：下载源 `dlcdn.apache.org` 返回 HTTP 404（Apache CDN 不保留历史版本）。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 通常只保留最新版本，历史版本（如 35.0.0）会被下架，导致构建时返回 404。Apache 归档站 (`archive.apache.org`) 永久保留所有历史发布版本，是可靠的下载源。已通过 curl 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小为 639 MB。

## 潜在风险
无。归档站 URL 格式与 CDN URL 格式已验证一致（仅域名和路径前缀不同），SP2 版本的同源 Dockerfile 仍使用 `dlcdn.apache.org`，但其构建可能在未来也会遇到相同的 404 问题（不在本次修复范围内）。