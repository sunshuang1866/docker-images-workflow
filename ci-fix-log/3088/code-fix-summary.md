# 修复摘要

## 修复的问题
Apache Druid 35.0.0 下载 URL 使用 `dlcdn.apache.org` 导致 HTTP 404，已更换为归档镜像站 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 `RUN wget` 中的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（URL 路径从 `/druid/${VERSION}/` 改为 `/dist/druid/${VERSION}/`）。

## 修复逻辑
`dlcdn.apache.org` 是 Apache CDN 分发站，仅保留各项目最新版本，历史版本（如 druid 35.0.0）被下架后返回 404。`archive.apache.org` 是 Apache 官方归档站，保留所有历史发布版本。已通过 `wget --spider` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件可正常访问。

## 潜在风险
`archive.apache.org` 由 Apache 软件基金会运营，相比 CDN 分发站，下载速度可能稍慢，但稳定性更高（不会因版本更新而下架旧版）。无其他风险。