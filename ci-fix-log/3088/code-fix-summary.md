# 修复摘要

## 修复的问题
将 Apache Druid 下载源从已下架版本的 CDN (`dlcdn.apache.org`) 切换至保留历史版本的归档站 (`archive.apache.org`)，修复 HTTP 404 导致的 Docker 构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行的 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
分析报告指出 CI 构建失败根因为 `dlcdn.apache.org`（Apache CDN 分发节点）只托管当前最新版本，Apache Druid 35.0.0 已从该 CDN 下架，导致 `wget` 返回 HTTP 404。根据分析报告方向 1（置信度: 高），将下载源替换为 `archive.apache.org/dist/druid/`（Apache 官方归档站，保留所有历史版本）。

已通过 WebFetch 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可访问（返回内容，非 404），确认归档站保留了 35.0.0 版本。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，历史上所有已发布版本均会迁移至此，URL 路径格式与 CDN 一致，仅域名不同。