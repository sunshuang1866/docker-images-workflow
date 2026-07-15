# 修复摘要

## 修复的问题
Dockerfile 中从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0 二进制包返回 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行 `wget` 下载源从 `https://dlcdn.apache.org/druid/` 改为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
`dlcdn.apache.org` CDN 只保留各项目的最新版本，Druid 35.0.0 已从该 CDN 下架。使用 `archive.apache.org/dist/druid/`（Apache 官方归档站）替代，该站点保留所有历史版本。已验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 当前可访问且文件存在。

## 潜在风险
- `archive.apache.org` 在部分 CI 环境中可能有网络超时问题（模式33案例），如后续构建中仍然失败，可考虑使用 `repo.huaweicloud.com/apache/druid/` 作为替代下载源。
- 此下载源不支持 TLS 证书内置校验，与原始 `dlcdn.apache.org` 行为一致，未引入新的安全隐患。