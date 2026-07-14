# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包在 `dlcdn.apache.org` 上已下架（HTTP 404），导致 Docker 构建失败。将下载源切换为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN（dlcdn.apache.org）仅托管最新版本，Druid 35.0.0 的制品已被下架，导致 wget 返回 404。`archive.apache.org` 完整保留 Apache 项目所有历史发布版本的制品，替换后构建可正常下载 Druid 35.0.0 二进制包。已通过 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，确认制品存在且可达。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站点，会长期保留历史制品。同日期的 `24.03-lts-sp2` Dockerfile 仍使用 `dlcdn.apache.org`，也可能面临同样的 404 问题，但不在本次 PR 修改范围内。