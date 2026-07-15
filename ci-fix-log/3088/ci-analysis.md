# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式01/模式38（Apache CDN 版本 404 系列）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz     && tar -zxvf apache-druid-35.0.0-bin.tar.gz     && mv apache-druid-35.0.0 /opt/druid     && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Docker 构建 builder 阶段从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0 二进制包时返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，不保证历史版本的可用性（与知识库中模式01 Maven 和模式38 ActiveMQ 的根因一致）。Druid 35.0.0 可能已被 CDN 下架，或该 CDN 路径格式对 Druid 不适用。

### 与 PR 变更的关联
PR #3088 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，在 builder 阶段的 `wget` 步骤中使用了 `dlcdn.apache.org` 下载源。该 URL 在构建时返回 404，失败与 PR 直接相关。

## 修复方向

### 方向 1（置信度: 中）
将下载源从 `dlcdn.apache.org` 切换为 Apache 归档站 `archive.apache.org`，URL 格式为：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
理由：`archive.apache.org` 是 Apache 的正式归档站，保留所有历史版本，已知在 CI 构建环境中可达（但需确认，以往也有超时案例）。此修复方式与模式01中 Maven 和模式38中 ActiveMQ 的修复思路一致。

### 方向 2（置信度: 低）
如果 `archive.apache.org` 也不可达（参考模式33中该域名的网络超时问题），可尝试使用华为云镜像站或清华镜像站作为下载源。

## 需要进一步确认的点
1. `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 的 404 是因为版本下架还是 URL 路径本身不正确，需要在浏览器中访问该 URL 或查阅 Apache Druid 官方下载页面确认。
2. 确认 `archive.apache.org` 在 CI 构建环境的网络可达性（历史上有 archive.apache.org 超时的案例，如模式33）。

## 修复验证要求
code-fixer 在提交前需验证：
1. 从浏览器或 curl 访问候选下载 URL（archive.apache.org 或镜像站），确认 Apache Druid 35.0.0 的 `apache-druid-35.0.0-bin.tar.gz` 确实存在。
2. 如果使用 `archive.apache.org`，需确保该域名在 CI 构建环境中可达；若不可达，需另行选择镜像站。
