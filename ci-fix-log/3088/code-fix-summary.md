# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包从 `dlcdn.apache.org` CDN 返回 HTTP 404，导致 Docker 构建失败。修复为使用 Apache 归档服务器 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行，将 `wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `wget https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本制品，Druid 35.0.0 已被 CDN 轮转清理下架，导致 wget 返回 404。Apache 归档服务器 (`archive.apache.org`) 长期保留所有已发布版本，不受 CDN 轮转影响。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 OK，确认可正常访问。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档服务器，长期稳定可用。同仓库内其他使用 `dlcdn.apache.org` 下载 Druid 的 Dockerfile（如 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）若后续重建可能遇到同样问题，但不在本次 PR 变更范围内。