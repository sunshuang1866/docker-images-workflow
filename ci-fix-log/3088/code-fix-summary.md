# 修复摘要

## 修复的问题
Docker 构建时 wget 请求 `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，下载步骤失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将下载源 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 切换为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
Apache Druid 35.0.0 的二进制包在 CDN（dlcdn.apache.org）上不可用（返回 404），但在 Apache 归档站（archive.apache.org）上存在。已从上游 archive.apache.org/dist/druid/35.0.0/ 目录验证，`apache-druid-35.0.0-bin.tar.gz`（610M，2025-10-27 发布）确实存在，修复后的 URL 可正常下载。此修复对应 CI 分析报告中置信度为"高"的方向1方案。

## 潜在风险
- archive.apache.org 在特定 CI 构建节点上可能连接超时，若出现此类情况可切换至华为云镜像站（repo.huaweicloud.com）作为备选下载源。