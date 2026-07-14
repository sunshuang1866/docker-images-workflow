# 修复摘要

## 修复的问题
Apache Druid 35.0.0 二进制包从 `dlcdn.apache.org` 下载返回 HTTP 404，因 Apache CDN 仅保留最新版本，历史版本已被移除。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: 将 builder 阶段第 9 行的 `wget` 下载源从 `https://dlcdn.apache.org/druid/` 切换为 `https://archive.apache.org/dist/druid/`

## 修复逻辑
Apache CDN (`dlcdn.apache.org`) 只托管当前最新版本的制品，Druid 35.0.0 已非最新版本，因此被 CDN 清理。Apache Archive (`archive.apache.org`) 保留了所有历史版本的归档制品。将下载源切换为 archive 站点即可获取历史版本。

已验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常访问（HTTP 200 OK），路径和文件名均正确。

## 潜在风险
无。`archive.apache.org` 是 Apache 官方归档站，长期保留历史版本，此修复方式与项目中其他同类问题（模式01/模式38）的修复方式一致。