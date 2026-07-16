# 修复摘要

## 修复的问题
CI 构建环境中 `archive.apache.org` 不可达，导致 Docker build 中 wget 下载 Druid 35.0.0 压缩包失败。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将第 9 行的下载源从 `https://archive.apache.org/dist/druid/` 替换为 `https://repo.huaweicloud.com/apache/druid/`

## 修复逻辑
CI 分析报告指出，`archive.apache.org`（以及可能重定向到它的 `dlcdn.apache.org`）在 CI 构建环境中网络不可达。分析报告推荐使用华为云镜像站 (`repo.huaweicloud.com`) 作为替代源。经验证，`https://repo.huaweicloud.com/apache/druid/35.0.0/` 下确实存在 `apache-druid-35.0.0-bin.tar.gz`，且该镜像站已在同仓库的多个 Dockerfile 中被使用（用于 Apache Maven 下载）。此修改仅变更下载 URL，不改变文件结构、构建逻辑或版本。

## 潜在风险
无。该镜像站已在本仓库大量 Dockerfile 中用于 Apache 系列软件下载，且 Druid 包的路径结构与原 Apache 官方 URL 下的路径结构一致。