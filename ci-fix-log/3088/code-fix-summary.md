# 修复摘要

## 修复的问题
Druid 35.0.0 构建阶段从 `dlcdn.apache.org` 下载 tarball 返回 HTTP 404，因 Apache CDN 不保留历史版本制品。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行下载源从 `https://dlcdn.apache.org/druid/` 改为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本制品，Druid 35.0.0 的 tarball 已下架导致 404。Apache 官方归档站 `archive.apache.org/dist/druid/` 保留所有历史版本，可直接替代。已通过 `curl -I` 验证新 URL 返回 HTTP 200（Content-Length: 639398150），tarball 完整可访问。

## 潜在风险
`archive.apache.org` 无 CDN 加速，在 CI 环境中下载 639MB 文件可能较慢，但该站点为 Apache 官方归档基础设施，可用性有保障。若后续 CI 环境无法访问 archive.apache.org（历史案例中曾出现），可考虑降级备用方案为华为云镜像站 `repo.huaweicloud.com/apache/druid/`。