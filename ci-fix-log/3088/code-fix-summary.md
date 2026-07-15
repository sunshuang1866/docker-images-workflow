# 修复摘要

## 修复的问题
Druid 35.0.0 下载源 `dlcdn.apache.org` 返回 HTTP 404，构建失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第9行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 更换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告确认 `dlcdn.apache.org` CDN 不托管 Druid 35.0.0 制品，返回 HTTP 404 导致 wget 失败（exit code: 8）。按照报告修复方向1（高置信度），将下载源更换为 Apache 归档站 `archive.apache.org/dist/druid/`。已从上游 archive.apache.org 获取 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 验证，文件存在且可下载（非 404），URL 格式和路径正确。

## 潜在风险
- `archive.apache.org` 在某些网络环境下可能出现超时（参考历史模式33），若后续构建再次失败可考虑华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为备用源。