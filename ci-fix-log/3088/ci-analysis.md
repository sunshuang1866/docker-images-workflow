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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 对 Druid 35.0.0 的下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。与模式01（Maven）和模式38（ActiveMQ）同根因——`dlcdn.apache.org` 是 Apache CDN 分发节点，不保证历史版本的长期可用性，Druid 35.0.0 的二进制包已在该 CDN 上被移除。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，下载 URL 直接硬编码使用 `dlcdn.apache.org` CDN。该 URL 在构建时已不可用，是 PR 变更直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org/dist/druid/` 或国内镜像站（如 `repo.huaweicloud.com/apache/druid/`），归档站和镜像站会保留历史版本。URL 格式参考：
- `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 低）
验证 Druid 35.0.0 是否存在以及 `dlcdn.apache.org` 上的实际可用版本。如果 Druid 35.0.0 发布后被更高版本替代（如已发布 35.0.1），确认是否需要升级到最新可用版本而非换源。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/` 或 `repo.huaweicloud.com/apache/druid/35.0.0/` 上是否存在 `apache-druid-35.0.0-bin.tar.gz`
- 确认 Druid 35.0.0 是否已被更高版本替代、是否需要升级版本号

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用 — 本次修复不涉及正则 patch 外部源文件）
