# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包下载源由 `dlcdn.apache.org`（CDN，已下架该版本）更换为 `archive.apache.org`（归档站，长期保留历史版本），解决 HTTP 404 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 `wget` URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 构建在 `wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 时返回 HTTP 404。Apache CDN (`dlcdn.apache.org`) 仅保留最新版本，Druid 35.0.0 已被移除。Apache 归档站 (`archive.apache.org`) 长期保留所有历史发布版本，经验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常访问。

## 潜在风险
无。同目录下已有 Druid 的 SP2 版本 Dockerfile 使用 `dlcdn.apache.org`，该版本同样面临未来被下架的风险，但不在本次修复范围内。