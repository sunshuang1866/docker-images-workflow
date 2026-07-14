# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz \
    && tar -zxvf apache-druid-35.0.0-bin.tar.gz \
    && mv apache-druid-35.0.0 /opt/druid \
    && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 对 Druid 35.0.0 返回 HTTP 404——该 CDN 为 Apache 的多区域 CDN 分发节点，通常仅保留最新版本制品，历史版本（如 Druid 35.0.0）已被下架（与模式01中 Maven 及模式38中 ActiveMQ 的根因一致）。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行 `wget` 命令的下载目标 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 直接触发了该失败。失败完全由本次 PR 的改动引起。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org`（仅保留最新版本的 CDN）切换为 `archive.apache.org`（Apache 归档站，保留所有历史版本），即 URL 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。此方案与历史案例（模式01、模式33、模式38）中"换归档源"的修复思路一致。

### 方向 2（置信度: 中）
确认 Druid 35.0.0 是否为 Apache 该产品的最新版本——如果上游已发布更新版本（如 35.0.1 等），可将 `VERSION` 升级至 CDN 上实际可用的版本，并保留 `dlcdn.apache.org` 作为下载源。但需先验证新版在 CDN 上确实可用。

## 需要进一步确认的点
- `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实存在——在修复前需手动 wget 该 URL 验证归档站上有此版本制品。
- Druid 是否有更新的 patch 版本可替代 35.0.0（若归档站也无此版本）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无。本修复不涉及正则 patch 外部源文件，仅需将 Dockerfile 中 wget 的 URL 从 CDN 域名切换为归档域名。
