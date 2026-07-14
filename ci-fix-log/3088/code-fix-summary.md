# 修复摘要

## 修复的问题
Apache Druid 35.0.0 下载 URL 不可达：`dlcdn.apache.org` 已移除该历史版本，导致 `wget` 返回 HTTP 404，Docker 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载源从 `https://dlcdn.apache.org/druid/` 切换为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
分析报告指出根因为 Apache CDN（`dlcdn.apache.org`）仅托管最新版本软件，Druid 35.0.0 已不再是当前最新版，因此 CDN 已下架该版本的文件。修复方案是将下载源从 CDN 切换到 Apache Archive（`archive.apache.org`），后者保留所有历史版本。已从上游获取 `apache-druid-35.0.0-bin.tar.gz` 验证，archive 站 URL 可达且返回正确文件。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留所有历史版本，与 CDN 不同不会随时间变化而移除旧版本。其他现有 Druid 版本的 Dockerfile 若也使用 `dlcdn.apache.org`，未来可能面临同样问题，但不在本次修复范围内。