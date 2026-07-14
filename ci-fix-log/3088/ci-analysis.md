# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`
- 失败原因: `dlcdn.apache.org`（Apache CDN）只托管当前最新版本，Druid 35.0.0 已从 CDN 下架，wget 下载返回 HTTP 404。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中下载源使用了 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。该 CDN 地址已不再提供 Druid 35.0.0 的二进制包，导致构建在 `builder` 阶段的 wget 步骤失败。这与 PR 的 Dockerfile 直接相关——下载 URL 需要更换为保留历史版本的归档源。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（仅保留最新版）切换为 `archive.apache.org/dist/druid/`（保留所有历史版本）。URL 模板从：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此方向与知识库中模式01（Apache CDN Maven 404）和模式38（ActiveMQ CDN 404）的修复策略一致：`dlcdn.apache.org` 是 CDN 分发节点，只保留最新版本；`archive.apache.org` 是历史归档站，保留所有已发布版本。

### 方向 2（置信度: 中）
若 `archive.apache.org` 也存在网络不可达问题（参考模式33 中 `downloads.apache.org` / `archive.apache.org` 在 CI 环境的通性问题），可考虑使用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。

## 需要进一步确认的点
1. 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建环境中是否可达。
2. 确认现有 SP2 版本的 Druid 35.0.0 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用相同的 `dlcdn.apache.org` 下载源——如果是，该 Dockerfile 在重建时也会遇到同样的 404 问题，建议一并修复。

## 修复验证要求
code-fixer 应在提交前验证新下载 URL 可访问：使用 `curl -I` 或 `wget --spider` 确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。
