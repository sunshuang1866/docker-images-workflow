# 修复摘要

## 修复的问题
Apache CDN (`dlcdn.apache.org`) 不再托管 Flink 2.1.0 二进制包导致 wget 返回 HTTP 404，构建失败。

## 修改的文件
- `Bigdata/flink/2.1.0/24.03-lts-sp4/Dockerfile:27`: 将 `ENV FLINK_TGZ_URL` 从 `https://dlcdn.apache.org/flink/...` 切换为 `https://archive.apache.org/dist/flink/...`

## 修复逻辑
分析报告指出根因是 `dlcdn.apache.org` 仅托管最新版本，Flink 2.1.0 已被移除。修复方向为将下载源切换至 Apache 归档站。已通过 `curl -sI` 验证 `https://archive.apache.org/dist/flink/flink-2.1.0/flink-2.1.0-bin-scala_2.12.tgz` 返回 HTTP 200，确认该版本在归档站可用。

## 潜在风险
`Bigdata/flink/2.1.0/24.03-lts-sp1/Dockerfile` 和 `Bigdata/flink/2.1.0/24.03-lts-sp2/Dockerfile` 使用了相同的 `dlcdn.apache.org` URL（不在本次 PR 变更文件范围内），重新构建时也会遇到相同 404，建议后续一并修复。