# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式（与模式01/模式38 同根因）
- 新模式标题: Apache CDN 版本404
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
------
ERROR: failed to solve: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本制品。Druid 35.0.0 的二进制包已从 CDN 下架，wget 下载时返回 HTTP 404，Docker 构建失败。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。`wget` 下载源使用了 `dlcdn.apache.org`（Apache CDN），该源不保证历史版本可用性。Druid 35.0.0 已不是最新版本，其制品在 CDN 上已不存在。此问题与现有 SP2 版本的下载源选择有关——若 SP2 版本使用了不同的下载源（如 `archive.apache.org`），则 SP4 的 Dockerfile 应与其保持一致。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/druid/`，后者保留所有历史版本。URL 格式：
- 当前（无效）: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 修复: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

历史案例中，ActiveMQ（模式38）和 Maven（模式01）均有相同的 `dlcdn.apache.org` 404 问题，修复方案均为更换下载源。

### 方向 2（置信度: 中）
若 `archive.apache.org` 也不可达（参考模式33 中 archive.apache.org 网络不通的历史案例），可考虑使用华为云镜像站：`https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

## 需要进一步确认的点
1. 现有 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 中使用的下载源是什么？SP4 的新 Dockerfile 应与 SP2 的下载源保持一致，避免同样的历史版本 404 问题再次发生。
2. Druid 35.0.0 在 `archive.apache.org/dist/druid/` 下是否确实存在？需人工验证该版本的正确下载路径。

## 修复验证要求
code-fixer 必须在提交前：
1. 用 `wget --spider` 或 `curl -I` 验证新 URL 返回 HTTP 200（而非 404）
2. 与 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 中的下载源进行对比，确保 SP4 版本与 SP2 版本采用一致的、可长期访问的下载源
