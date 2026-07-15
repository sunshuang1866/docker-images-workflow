# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包从 `dlcdn.apache.org` CDN 返回 404，构建下载步骤失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `wget` 下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发节点，通常仅保留最新版本，Druid 35.0.0 已从该 CDN 下架导致 404。`archive.apache.org` 是 Apache 官方归档站，保留所有历史版本。经验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，可正常下载。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方维护的归档站点，与 CDN 相比下载速度可能略慢但不影响构建成功。