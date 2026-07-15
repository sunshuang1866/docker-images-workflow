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
- 失败原因: `dlcdn.apache.org` CDN 节点不再托管 Apache Druid 35.0.0 的二进制包（`dlcdn.apache.org` 只保留各项目的最新版本，历史版本下架后返回 404），导致 `wget` 下载失败（exit code: 8）。

### 与 PR 变更的关联
PR 新增的 Dockerfile 中第 9 行使用了 `dlcdn.apache.org` 作为下载源。该 CDN 节点不保证历史版本的可用性——Druid 35.0.0 发布后，CDN 可能已将其下架（或从未托管过该版本）。此为 PR 代码直接引发的失败。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org/dist/druid/`（Apache 归档站，保留所有历史版本），URL 改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
如 `archive.apache.org` 在 CI 环境中不可达（参考模式33中多起 `archive.apache.org` 网络超时案例），可使用华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为替代下载源。

## 需要进一步确认的点
- 同目录下已有的 Druid 35.0.0-oe2403sp2 Dockerfile 是否也使用 `dlcdn.apache.org` 作为下载源——若是，该镜像在 CI 中可能在近期同样出现 404（如果 CDN 刚下架该版本）或此前构建时 CDN 尚存该版本故未失败。
- `archive.apache.org` 当前是否确实托管了 `druid/35.0.0/` 目录下的二进制包。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本修复不涉及正则 patch 外部源文件）
