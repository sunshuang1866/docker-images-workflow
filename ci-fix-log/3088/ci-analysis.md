# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404）

## 根因分析

### 直接错误
```
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org`（Apache 官方 CDN）仅托管当前最新版本软件，Apache Druid 35.0.0 已不再是最新版本，被 CDN 下架，导致 `wget` 下载时返回 HTTP 404。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其第 9 行直接使用 `dlcdn.apache.org` 作为下载源。该 URL 在构建时已失效（版本被 CDN 移除），PR 的 Dockerfile 变更直接触发了此失败。注意：已存在的 `35.0.0-oe2403sp2` 版本可能在 Druid 35.0.0 仍为最新版时构建成功，但 CDN 现已剔除该版本。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 归档站，保留所有历史版本），URL 格式为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
保持 `dlcdn.apache.org` 作为下载源，但将 `VERSION` 升级为 CDN 当前可用的最新 Druid 版本（需确认上游最新版本号）。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实可达（Apache Archive 通常保留所有历史版本）。
- 确认已存在的 `35.0.0-oe2403sp2` Dockerfile 中使用的下载源——如果它也用 `dlcdn.apache.org`，则说明该 URL 在构建时有效、现已失效，进一步佐证 CDN 下架判断。
