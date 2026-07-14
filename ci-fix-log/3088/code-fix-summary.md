# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包从 `dlcdn.apache.org` CDN 下载返回 HTTP 404，该 CDN 不再托管历史版本制品。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/...` 替换为 `https://archive.apache.org/dist/druid/${VERSION}/...`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 是 Apache CDN 节点，仅托管最新版本的制品，Druid 35.0.0 的历史包已被下架，导致 `wget` 返回 404。修复方向是将下载源替换为 `archive.apache.org`，该归档站保留所有 Apache 项目的历史版本。已通过 `wget --spider` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200（610M），确认目标文件存在且可访问。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，路径结构 `/dist/druid/{version}/` 为 Apache 项目标准路径，同仓库内其他应用镜像（如 ActiveMQ）也在使用相同归档源。