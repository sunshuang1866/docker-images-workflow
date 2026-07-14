# 修复摘要

## 修复的问题
Druid 35.0.0 二进制包从 `dlcdn.apache.org` 下载返回 HTTP 404（CDN 已下架历史版本），已于前次修复运行中将下载源切换为 `archive.apache.org`。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 第 9 行 `wget` 下载 URL 已从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（commit `668a67725`，由前次 ci-fix-team 自动修复完成）。

## 修复逻辑
CI 分析报告指出根因是 `dlcdn.apache.org`（Apache CDN 分发节点）仅保留最新版本，Druid 35.0.0 历史版本已从该 CDN 下架，导致 `wget` 返回 HTTP 404。修复方向是将下载源切换为 `archive.apache.org/dist/druid/`，该站点保留所有历史版本。

已验证：`https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200（文件大小 610MB，可正常获取），而 `dlcdn.apache.org` 对应 URL 返回 HTTP 404。

## 潜在风险
- `archive.apache.org` 在部分 CI 节点上可能存在网络连通性问题（历史模式 33 记录），如果后续构建仍失败，可考虑切换为 `repo.huaweicloud.com/apache/druid/` 等国内镜像。
- SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）仍使用 `dlcdn.apache.org`，但该文件不在当前 PR 的变更范围内，不可修改。后续触发 SP2 构建时可能遇到相同 404 错误。