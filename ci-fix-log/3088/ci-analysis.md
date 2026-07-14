# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN Maven 版本 404，同类根因同样适用于 Druid/ActiveMQ 等 Apache 项目）
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
- 失败原因: `dlcdn.apache.org` CDN 不保留 Apache Druid 35.0.0 的历史版本制品，下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。这是 `dlcdn.apache.org` 的已知行为——该 CDN 通常只托管各 Apache 项目的最新版本，旧版本下架后即不可用。

### 与 PR 变更的关联
PR 新增的 Dockerfile 直接使用了 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。URL 格式本身正确（`${VERSION}` 正确展开为 `35.0.0`），但 Apache Druid 35.0.0 的制品已从该 CDN 节点下架。此问题由 PR 变更直接触发——Dockerfile 中选择的下载源不可用。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，后者是 Apache 官方归档站，保留所有历史版本。URL 格式改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此修复与模式01、模式27、模式38 的历史案例一致——当 Apache CDN 不可用时，统一回退到 `archive.apache.org`。

### 方向 2（置信度: 低）
若 `archive.apache.org` 同样不可达（参考模式33 中 `downloads.apache.org` 的网络超时问题），可将下载源更换为华为云镜像站 `repo.huaweicloud.com/apache/druid/` 或清华大学镜像站 `mirrors.tuna.tsinghua.edu.cn/apache/druid/`，前提是这些镜像站确实托管了 Druid 35.0.0。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否实际存在且可下载。
- 若 `archive.apache.org` 也不可用，需要逐一验证各镜像站是否托管了 Apache Druid 35.0.0 的制品。

## 修复验证要求
code-fixer 在提交前，必须使用 `wget --spider` 或 `curl -I` 验证新下载 URL 返回 HTTP 200（而非 404），确保替换后的 URL 确实可达。例如：
```bash
wget --spider https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
```
