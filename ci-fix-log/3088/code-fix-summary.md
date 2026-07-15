# 修复摘要

## 修复的问题
Druid 35.0.0 下载 URL 从 `dlcdn.apache.org`（Apache CDN，已下架历史版本）更换为 `archive.apache.org`（Apache Archive，保留所有版本），解决 HTTP 404 构建错误。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行，将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI Failure Analyst 报告指出 Apache CDN（`dlcdn.apache.org`）仅保留当前最新版本，Druid 35.0.0 已从该 CDN 下架，导致下载返回 HTTP 404。修复方案与分析报告"方向 1"一致：将下载源更换为 Apache Archive（`archive.apache.org`），该站点保留所有历史版本。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 OK，Content-Length: 639398150。

## 潜在风险
无。Apache Archive 是 Apache 官方的历史版本归档站点，长期稳定可用。若未来 CI 构建环境中 `archive.apache.org` 网络不可达，可考虑使用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为备选。