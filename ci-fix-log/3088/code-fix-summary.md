# 修复摘要

## 修复的问题
Druid 35.0.0 下载源从 Apache CDN (`dlcdn.apache.org`) 返回 404，更换为 Apache 归档站 (`archive.apache.org`) 使构建通过。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 wget URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本，Druid 35.0.0 已下架导致 HTTP 404。按照 CI 分析报告方向 1（高置信度），将下载源切换至 `archive.apache.org/dist/druid/`，这是 Apache 官方历史版本归档站，保留所有正式发布版本。经 WebFetch 验证，`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常访问（返回二进制内容）。

## 潜在风险
- SP2 版本的 Dockerfile (`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`) 仍使用 `dlcdn.apache.org`，后续该版本也可能遇到相同 404 问题，但不在当前 PR 变更范围内。
- 若 `archive.apache.org` 在 CI 网络环境中不可达，可降级使用华为云镜像 `repo.huaweicloud.com/apache/druid/` 作为备选（CI 分析报告方向 2）。