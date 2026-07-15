# 修复摘要

## 修复的问题
Dockerfile 中 Druid 下载源使用 `dlcdn.apache.org` 导致 404 构建失败，已替换为 Apache 归档站。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` CDN 节点不保留 Druid 历史版本的二进制包，35.0.0 版本已下架返回 404。按照报告推荐的修复方向 1，将下载源切换为 `archive.apache.org/dist/druid/`（Apache 官方归档站，保留所有历史版本）。

## 潜在风险
`archive.apache.org` 在某些 CI 环境中可能存在网络超时问题。如后续出现此类问题，可进一步替换为 `repo.huaweicloud.com/apache/druid/` 华为云镜像站作为备选方案。