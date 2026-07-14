# 修复摘要

## 修复的问题
Docker 构建失败：`dlcdn.apache.org` 对 `apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
根因是 Apache CDN (`dlcdn.apache.org`) 不再托管 Druid 35.0.0 的旧版本制品，导致 wget 返回 404。将下载源切换为 Apache 归档站 (`archive.apache.org`)，该站点长期保留历史版本。已从上游获取 `https://archive.apache.org/dist/druid/35.0.0/` 目录列表验证，`apache-druid-35.0.0-bin.tar.gz` (610M) 确实存在于归档站中。

## 潜在风险
无。归档站 URL 格式 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 是 Apache 项目的标准归档路径，稳定可靠。