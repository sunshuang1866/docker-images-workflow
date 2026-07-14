# 修复摘要

## 修复的问题
Apache CDN (`dlcdn.apache.org`) 已移除 Druid 35.0.0 二进制包，导致 `wget` 返回 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行，将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/`

## 修复逻辑
CI 分析报告根因：`dlcdn.apache.org` 仅保留各项目最新版本，旧版本制品会被下架，导致 Druid 35.0.0 的 `apache-druid-35.0.0-bin.tar.gz` 返回 404。

修复方向：将下载源切换为 Apache Archive (`https://archive.apache.org/dist/druid/`)，该站点保留所有历史版本，不会下架。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，Content-Length: 639398150，确认制品可用。

## 潜在风险
无。Apache Archive 是官方长期归档站点，Druid 35.0.0 制品在该站点稳定存在。