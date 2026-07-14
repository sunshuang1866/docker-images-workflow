# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包下载源 `dlcdn.apache.org` 已下架该版本（返回 HTTP 404），导致 Docker 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
根据 CI 分析报告，`dlcdn.apache.org`（Apache CDN 分发节点）仅托管当前最新版本，Druid 35.0.0 历史版本已被清理。将下载源更换为 Apache 官方归档站 `archive.apache.org/dist/druid/`，该站点长期保留历史版本。已验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件可正常下载。

## 潜在风险
无。归档站为 Apache 官方基础设施，长期稳定维护历史版本。