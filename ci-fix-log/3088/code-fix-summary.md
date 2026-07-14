# 修复摘要

## 修复的问题
Dockerfile 中 `wget` 从 `dlcdn.apache.org/druid/35.0.0/` 下载 `apache-druid-35.0.0-bin.tar.gz` 时返回 HTTP 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/`

## 修复逻辑
分析报告指出 `dlcdn.apache.org/druid/35.0.0/` 路径下不存在 `apache-druid-35.0.0-bin.tar.gz`（返回 404），根因是 CDN 未托管此版本制品。

修复方案：将下载 URL 从 CDN（`dlcdn.apache.org`）切换为 Apache 归档站（`archive.apache.org/dist/druid/`），归档站保留所有历史发行版制品。

验证结果：已通过 HTTP HEAD 请求确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200 OK，文件存在且可正常下载。

## 潜在风险
无。此修改仅更换了下载源域名和路径前缀，`archive.apache.org` 是 Apache 官方归档站，长期稳定可用。