# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包在 `dlcdn.apache.org` CDN 上返回 404，将下载源更换为 Apache 归档镜像站。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`: 将 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
`dlcdn.apache.org` CDN 仅保留 Apache 项目最新版本，Druid 35.0.0 的二进制包已被下架（返回 HTTP 404）。`archive.apache.org` 是 Apache 官方归档站，保留所有历史发布版本。经 `wget --spider` 验证，`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常访问（HTTP 200），确认归档路径有效。

## 潜在风险
- `archive.apache.org` 从 CI 构建环境网络连通性需在 CI 实际运行时进一步确认。若不可达，备选方案为华为云镜像站 `repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`。
- 无其他风险，仅改动下载域名和路径，URL 参数结构未变。