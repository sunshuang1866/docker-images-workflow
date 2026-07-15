# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式38 / 模式01

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ...
did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 对 Apache Druid 35.0.0 返回 HTTP 404。Apache CDN (`dlcdn.apache.org`) 不保证历史版本的持久可用性，该版本可能在 CDN 上已被移除或从未同步。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行的 `wget` 命令直接使用了 `dlcdn.apache.org` 作为下载源。该 URL 在构建时返回 404，与 PR 改动直接相关。

## 修复方向

### 方向 1（置信度: 高）
将 Apache Druid 的下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 官方归档站，保留所有已发布版本）：

- 当前 URL: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 建议 URL: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

这与模式01（Maven CDN 404）、模式38（ActiveMQ CDN 404）的修复思路一致：`dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本；`archive.apache.org` 是归档站，保留所有历史版本。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 同样返回 404（说明该版本可能尚未归档或归档存在延迟），可考虑将 URL 替换为华为云镜像站 `repo.huaweicloud.com/apache/druid/` 或其他可靠的国内镜像源。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否实际存在并可访问。
- 确认 Apache Druid 35.0.0 是否为最新稳定版——如果是，`dlcdn.apache.org` 理应托管该版本，404 可能意味着 CDN 同步延迟；如果已有更新版本（如 35.1.0），CDN 可能已移除旧版本。

## 修复验证要求
code-fixer 在提交前，必须使用 `wget --spider` 或 `curl -I` 验证新 URL（`archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）确实返回 HTTP 200，确保制品可下载后再提交。
