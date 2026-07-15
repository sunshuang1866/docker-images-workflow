# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404）/ 模式38（ActiveMQ 下载源 404）

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（wget 下载步骤）
- 失败原因: Apache CDN (`dlcdn.apache.org`) 仅保留当前最新版本，Druid 35.0.0 已从 CDN 下架，下载 URL 返回 HTTP 404。这与模式01（Apache CDN Maven 版本 404）和模式38（ActiveMQ 下载源 404）的根本原因完全一致。

### 与 PR 变更的关联
直接关联。PR #3088 新增的 Dockerfile 中使用 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源，该 CDN 节点不保证历史版本的可用性。这是 Dockerfile 中下载 URL 选择不当导致的问题，而非 Druid 35.0.0 本身不存在。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org`（Apache CDN，仅保留最新版）更换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。URL 模板应改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此修复方向与模式01/模式38的历史案例处理方法一致——Apache CDN 下架的版本可通过 Apache Archive（`archive.apache.org`）获取。

### 方向 2（置信度: 中）
若 `archive.apache.org` 因网络不可达（如模式33中出现的 `archive.apache.org` 连接超时问题），可将下载源更换为华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。此方案适用于 CI 构建环境中 `archive.apache.org` 不可达的场景。

## 需要进一步确认的点
1. 需确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在当前 CI 构建环境中网络可达（非所有 runner 均能访问 `archive.apache.org`）。
2. 日志仅包含 x86-64 架构构建的失败信息，aarch64 架构的构建日志未提供。若 aarch64 构建也失败，根因相同（同一 Dockerfile、同一下载 URL）。

## 修复验证要求
code-fixer 在提交修复前，需验证更换后的下载 URL（`archive.apache.org` 或备选镜像站）在当前 CI 构建环境中网络可达，且下载的 tar.gz 文件可正常解压。可先用 `wget --spider` 或 `curl -sI` 验证 URL 返回 200 OK 后再提交。
