# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38（变体）
- 新模式标题: Apache CDN Druid 版本 404
- 新模式症状关键词: dlcdn.apache.org, 404 Not Found, druid, wget, exit code: 8

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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget ...` 步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，Druid 35.0.0 的二进制包已从该 CDN 下架，导致下载 HTTP 404。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（全新文件），该 Dockerfile 中使用 `dlcdn.apache.org` 作为下载源。此问题是 PR 变更直接触发的——下载 URL 在 CI 构建时不可达。已知 Druid 35.0.0 此前在 sp2 变体中可正常构建，说明版本本身存在，问题在于 CDN 节点已不再托管该版本制品。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org/dist/druid/`（Apache 归档站，保留所有历史版本）。参考同类问题的修复（模式01 Maven、模式38 ActiveMQ），Apache 归档站是可靠的历史版本下载源。Dockerfile 中的 wget URL 应改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
使用国内镜像站（如 `repo.huaweicloud.com/apache/druid/`）作为备选下载源。需先确认该镜像站是否托管了 Druid 35.0.0 的二进制包。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可下载。
- 确认已有的 sp2 变体（`35.0.0-oe2403sp2`）Dockerfile 使用的是什么下载源，若其使用 `dlcdn.apache.org` 且当前仍可构建，则需确认 Druid 35.0.0 是否在 sp2 构建后新近被 CDN 移除。

## 修复验证要求
code-fixer 必须在提交前：
1. 用 `wget --spider` 或 `curl -I` 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200（而非 404）。
2. 如果归档站也不可用，检查 `https://repo.huaweicloud.com/apache/druid/35.0.0/` 是否托管该版本。
3. 确认替换后的 URL 在 Docker 构建环境中网络可达。
