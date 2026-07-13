# CI 失败分析报告

## 基本信息
- PR: #2926 — chore(spring-framework): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [3/7] RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.12/binaries/apache-maven-3.9.12-bin.tar.gz ...
#9 0.082 --2026-07-10 10:34:30--  https://dlcdn.apache.org/maven/maven-3/3.9.12/binaries/apache-maven-3.9.12-bin.tar.gz
#9 0.112 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.113 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.123 HTTP request sent, awaiting response... 404 Not Found
#9 0.125 2026-07-10 10:34:30 ERROR 404: Not Found.
------
Dockerfile:12
  11 |     ARG MAVEN_VERSION=3.9.12
  12 | >>> RUN wget https://dlcdn.apache.org/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
```

### 根因定位
- 失败位置: `Others/spring-framework/7.0.3/24.03-lts-sp4/Dockerfile:12`
- 失败原因: `dlcdn.apache.org` 只托管当前最新版 Maven，Maven 3.9.12 已从 CDN 下架，下载 URL 返回 HTTP 404。

### 与 PR 变更的关联
PR #2926 新增的 Dockerfile 中硬编码了 `MAVEN_VERSION=3.9.12`，并从 `dlcdn.apache.org` 下载该版本。该版本在当初写入 Dockerfile 时可能可用，但 CI 实际构建时 Apache CDN 已将其移除（CDN 仅保留最新版本）。此失败完全由 PR 新增的 Dockerfile 触发。

## 修复方向

### 方向 1（置信度: 高）
将 Maven 下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org/dist/maven/`（归档站，保留所有历史版本），Maven 版本 3.9.12 保持不变。归档站 URL 格式为：`https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
将 `MAVEN_VERSION` 升级为 Apache CDN 当前可用的最新版本（如 3.9.14 或更高），继续使用 `dlcdn.apache.org` 下载。需先确认目标版本在 CDN 上确实存在。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/maven/maven-3/3.9.12/binaries/apache-maven-3.9.12-bin.tar.gz` 确实存在。
- 如选择方向 2，确认 `dlcdn.apache.org` 上当前可用的 Maven 最新版本号。
