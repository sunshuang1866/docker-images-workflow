# 修复摘要

## 修复的问题
Druid 35.0.0 Dockerfile 中下载源使用了 `dlcdn.apache.org`（Apache CDN），该 CDN 不保留旧版本制品，导致 Druid 35.0.0 二进制包返回 HTTP 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`: 将 `wget` 下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache CDN（`dlcdn.apache.org`）采用 pull-through 缓存模型，不保证历史版本制品的持久可得性。Apache Archive（`archive.apache.org`）会永久保留所有已发布版本。将下载源切换为 Apache Archive 可确保构建时能稳定下载到 Druid 35.0.0 的二进制包。

已通过 `wget --spider` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200，文件大小 639MB，确认为有效的 tar.gz 包。

## 潜在风险
- `archive.apache.org` 在某些 CI 网络环境中曾出现过不可达的情况（参考模式33）。若后续 CI 构建再次失败且报网络错误，可考虑切换为华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为备选方案。
- SP2 版本的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）可能也存在同样的 `dlcdn.apache.org` 问题，由于该文件不在本次 PR 变更范围内，未做修改。建议单独评估。