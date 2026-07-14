# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404）
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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（builder 阶段的 `RUN wget` 步骤）
- 失败原因: `dlcdn.apache.org` CDN 是 Apache 的实时分发节点，通常只保留各项目的最新版本，Druid 35.0.0 已从该 CDN 下架，导致 wget 下载 `apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。

### 与 PR 变更的关联
**直接关联。** 本次 PR 新增的 Dockerfile 中，Druid 35.0.0 的下载源指定为 `dlcdn.apache.org`（CDN 分发节点），而非 `archive.apache.org`（归档节点）。由于 CDN 不保留历史版本，导致构建时下载失败。这是 PR 引入的下载源选择问题。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org`（CDN 实时节点）切换为 `archive.apache.org`（Apache 归档站），归档站保留所有历史发布版本，不会出现 404 问题。参考 URL 格式：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

### 方向 2（置信度: 中）
如果归档站同样不可达（如模式33中 network timeout），可换用华为云镜像站（`repo.huaweicloud.com`）的 Apache 镜像作为替代下载源。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否真实可访问且可下载。
- 确认 Druid 35.0.0 的上游官方发布包文件名格式与模板 `apache-druid-${VERSION}-bin.tar.gz` 一致。

## 修复验证要求
- code-fixer 必须在提交前，从 Apache 归档站验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实可下载，确保文件名与路径正确。
- 如果归档站不可达（网络问题），需测试华为云镜像站 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否可用。
