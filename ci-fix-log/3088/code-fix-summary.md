# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包在 `dlcdn.apache.org` CDN 上返回 404（已下架），更换下载源为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第9行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 仅保留最新版本的制品，旧版本下架后即返回 404。Apache 官方归档站 `archive.apache.org` 保留所有历史版本，是获取旧版本制品的目标地址。已通过 `curl -sI` 验证目标 URL `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件可正常下载。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期稳定维护；其他使用同样下载模式的 SP2 Dockerfile 若后续触发 rebuild 也会遇到相同问题，但本次修复仅针对 SP4 的 Dockerfile。