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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（RUN wget 下载步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本。Druid 35.0.0 的二进制包已在 CDN 上被下架，`wget` 下载 `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中硬编码使用 `dlcdn.apache.org` 作为 Druid 35.0.0 的下载源。该 CDN 节点不保证历史版本的持续可用性，Druid 35.0.0 已被移除。此失败是 PR 改动直接触发的。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`，后者长期保留所有历史发布版本的制品。

具体改动：
- 将 Dockerfile 第 9 行的 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
若 `archive.apache.org` 在 CI 构建环境中存在网络不可达问题（参考模式33），可改用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

## 需要进一步确认的点
1. 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可访问（Apache 官方 archive 中是否包含此版本）。
2. 检查同目录下已有的 Druid SP2 Dockerfile (`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`) 使用的是哪个下载源，可作为参考。

## 修复验证要求
code-fixer 必须在修改前手动验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可访问（返回 200），确认制品在归档站中确实存在后再提交。若归档站也不可用，则需尝试华为云镜像站等备用源。
