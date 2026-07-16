# 修复摘要

## 修复的问题
Apache Druid 下载源 `dlcdn.apache.org` 对历史版本返回 404，导致构建失败。同时修复 Dockerfile 中 `FromAsCasing` 警告。

## 修改的文件
- `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`: (1) 将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（上一提交已完成）；(2) 将第 3 行 `as` 改为 `AS` 以消除 BuildKit 的 `FromAsCasing` 警告

## 修复逻辑
1. **下载源切换**：Apache CDN (`dlcdn.apache.org`) 仅保留最新版本，Druid 35.0.0 的 binary tarball 已被下架，返回 404。将 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，使用 Apache 归档站（保留所有历史版本）。已通过 `curl -sI` 验证 `archive.apache.org` 的制品存在且可访问（HTTP 200）。
2. **FromAsCasing 警告**：Dockerfile 第 3 行 `FROM ${BASE} as builder` 中关键字大小写不一致（`FROM` 大写但 `as` 小写），改为 `AS` 保持一致，消除 BuildKit 警告。

## 潜在风险
- `archive.apache.org` 响应包含 `Vary: Slow,Glacial` header，下载速度可能慢于 CDN。若 CI 构建超时，可考虑使用华为云镜像源（如 `repo.huaweicloud.com/apache/druid/`）作为备选。
- 现有 SP2 Dockerfile (`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`) 可能也存在相同问题，但不在本次 PR 变更范围内，未作修改（建议另行修复）。