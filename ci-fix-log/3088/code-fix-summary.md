# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包在 `dlcdn.apache.org` 返回 404，下载源已失效，导致 Docker 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org`（Apache CDN 分发节点）仅保留最新版本，Druid 35.0.0 的制品已被下架，导致 HTTP 404。修复方案是将下载源切换至 `archive.apache.org`（Apache 归档站，保留所有历史版本）。该方案已通过 `curl -I` 验证返回 HTTP 200，确认制品在归档站可正常下载。

## 潜在风险
- `archive.apache.org` 下载速度可能慢于 CDN，仅在镜像首次构建时影响。
- Druid 35.0.0 在 `archive.apache.org` 的路径格式为 `/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，若 Apache 归档站路径格式调整，需同步修改。