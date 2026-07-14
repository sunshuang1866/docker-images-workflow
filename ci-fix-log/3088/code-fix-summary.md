# 修复摘要

## 修复的问题
将 Druid 35.0.0 的下载源从已下架版本的 `dlcdn.apache.org` 切换为保留历史版本的 `archive.apache.org`，解决 CI 构建时 HTTP 404 错误。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行下载 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 `dlcdn.apache.org` 已下架 Druid 35.0.0 的二进制包（HTTP 404），这与 Apache CDN 仅保留最新版本制品的已知行为一致。修复方向为将下载源切换至 Apache 归档站 `archive.apache.org`，该站保留所有历史版本。已从上游 `https://archive.apache.org/dist/druid/35.0.0/` 验证，`apache-druid-35.0.0-bin.tar.gz` 文件确实存在且文件名匹配 Dockerfile 中 `${VERSION}` 变量展开结果。

## 潜在风险
- `archive.apache.org` 在部分 CI 网络环境中可能不可达（模式33 中有历史案例）。如后续构建再次失败，可降级为方向2：使用华为云镜像站 `repo.huaweicloud.com` 的 Apache 镜像路径。