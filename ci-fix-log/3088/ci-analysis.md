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
- 失败原因: `dlcdn.apache.org` CDN 只托管 Apache 项目的最新版本，Druid 35.0.0 的二进制包已从该 CDN 下架，wget 请求返回 HTTP 404。

### 与 PR 变更的关联
本次 PR 新增了 druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中下载源直接使用了 `dlcdn.apache.org`。该 CDN 与模式01中 Maven 的情形相同——仅保留当前最新版本，历史版本会被清理。Druid 35.0.0 的 tarball 已不在该 CDN 上，导致构建阶段下载失败。PR 改动直接触发了此失败。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 官方归档站，保留所有历史版本）。URL 格式改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
若 `archive.apache.org` 在当前 CI 构建环境中不可达（参考模式33），可改用华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为替代下载源。

## 需要进一步确认的点
- 需要确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建环境中实际可达。
- 如果 `SP2` 版本目录下的 Dockerfile 也使用了 `dlcdn.apache.org` 作为 Druid 下载源（sp2 目录在 diff 中引用但未修改），需确认该 Dockerfile 的下载源是否同样会遭遇 404。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次修复不涉及正则 patch 外部源文件）
