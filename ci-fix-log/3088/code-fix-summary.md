# 修复摘要

## 修复的问题
Dockerfile 中 Druid 35.0.0 下载 URL `dlcdn.apache.org` 返回 HTTP 404，该 CDN 不保证历史版本可用。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（第9行）

## 修复逻辑
分析报告指出 `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，不保证历史版本可用。`archive.apache.org` 是 Apache 官方归档站，长期保留所有已发布版本。已使用 `wget --spider` 验证新 URL 返回 HTTP 200 (Content-Length: 610MB)，确认 Druid 35.0.0 在归档站可用。此修复与仓库中其他类似问题（模式01/33/38）的处理方式一致。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，比 CDN 更稳定。URL 结构仅在域名和路径上做了替换，其他参数（VERSION、文件名）保持不变。