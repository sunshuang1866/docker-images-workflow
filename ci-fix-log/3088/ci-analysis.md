# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38 (同类根因：Apache CDN `dlcdn.apache.org` 下架/不保留历史版本，返回 404)
- 新模式标题: (不适用，已有模式覆盖)
- 新模式症状关键词: (不适用)

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
- 失败原因: `dlcdn.apache.org` 的 Apache Druid 35.0.0 二进制包 (`apache-druid-35.0.0-bin.tar.gz`) 返回 HTTP 404。`dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，旧版本或特定版本可能在 CDN 上不可用。与历史模式01（Maven）、模式38（ActiveMQ）的根因完全一致——Apache CDN 下架了该版本的制品。

### 与 PR 变更的关联
本次 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中 `RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 直接触发了 404 错误。这是 PR 新增代码引发的问题，与已有 SP2 版本 Dockerfile 可能使用了相同的下载源但该源已失效（SP2 构建时该版本尚在 CDN 上可用，现在已下架）。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。参考模式01（Maven）和模式38（ActiveMQ）的修复方式：

- 当前 URL: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 替换为: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

同时建议检查已有 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否使用了相同的 `dlcdn.apache.org` 下载源——如果 SP2 也使用该源，后续重建时同样会失败，建议一并修复。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 同样返回 404（表明 Druid 35.0.0 从未发布到 Apache 归档站），则需确认 Apache Druid 35.0.0 的实际发布状态和正确的下载路径，或考虑降级到可用的相邻版本。

## 需要进一步确认的点
1. 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否可用（方向1修复前需验证）。
2. 确认 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）的下载源是否同样使用 `dlcdn.apache.org`，以判断是否需要同步修复。

## 修复验证要求
若修复方向为修改下载 URL，code-fixer 必须在提交前执行以下验证：
1. 使用 `wget --spider` 或 `curl -I` 验证新的 `archive.apache.org` URL 返回 HTTP 200，而非 404。
2. 如果新 URL 也返回 404，需要查阅 Apache Druid 官方发布页面确认 35.0.0 的正确制品 URL 格式。
