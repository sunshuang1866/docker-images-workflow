# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式（关联模式01、模式38）
- 新模式标题: "CDN版本404"
- 新模式症状关键词: dlcdn.apache.org, 404 Not Found, druid, wget, exit code: 8

## 根因分析

### 直接错误

```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget` 步骤）
- 失败原因: `dlcdn.apache.org` CDN 上不存在 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（HTTP 404）。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常仅保留最新版本，不保证历史版本的可用性。Druid 35.0.0 的二进制包已从该 CDN 下架。

### 与 PR 变更的关联

**PR 直接触发**。本次 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，该 Dockerfile 第 9 行：
```dockerfile
RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
在 CI 构建时，`dlcdn.apache.org` 已不再托管 Druid 35.0.0 的二进制包，导致下载失败。已有的 SP2 版本（`35.0.0-oe2403sp2`）可能在更早时期构建时该 URL 尚有效，或在 SP2 的 Dockerfile 中使用了不同的下载源。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org/dist/druid/`，归档站保留所有历史版本。URL 格式：
- 原: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 改: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
检查 Druid 35.0.0 是否有更新的 patch 版本（如 35.0.1）仍在 `dlcdn.apache.org` 上可用，如存在则将 `ARG VERSION` 升级到最新可用版本。此方向需先手工验证 CDN 上当前可用的 Druid 版本。

## 需要进一步确认的点
1. 检查现有的 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 中使用的下载源，确认 SP2 版本是否也使用 `dlcdn.apache.org` 及该 URL 当前是否仍有效
2. 在 `https://archive.apache.org/dist/druid/35.0.0/` 和 `https://dlcdn.apache.org/druid/` 上手工确认 Druid 35.0.0 的实际可用性
