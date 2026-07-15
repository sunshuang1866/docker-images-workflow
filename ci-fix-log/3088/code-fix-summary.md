# 修复摘要

## 修复的问题
Druid 35.0.0 构建时从 `dlcdn.apache.org` 下载二进制包返回 HTTP 404，因为该 CDN 仅保留最新版本，旧版本已下架。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
根因是 `dlcdn.apache.org` 不保留历史版本，Druid 35.0.0 已从该 CDN 下架。`archive.apache.org` 是 Apache 官方归档站，保留所有历史发布版本。已在当前环境通过 `wget --spider` 验证新 URL 返回 HTTP 200 OK，确认可正常下载。

## 潜在风险
如果 CI 构建环境无法访问 `archive.apache.org`（部分 CI 实例存在此问题），可备用 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 作为替代下载源。