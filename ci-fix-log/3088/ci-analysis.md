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
------
Dockerfile:9
--------------------
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Dockerfile 中 Druid 35.0.0 的下载源 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。`dlcdn.apache.org` 是 Apache CDN 分发节点，只保留当前最新版本，不保证历史版本的可用性。Druid 35.0.0 已被 CDN 下架。

### 与 PR 变更的关联
直接由 PR 新增的 Dockerfile 引起。该 Dockerfile 中硬编码了 `dlcdn.apache.org` 作为下载源（与同仓库内已有的 SP2 版本 Dockerfile 的写法一致），但该 CDN 节点不保证历史版本留存。虽然写法与已有 Dockerfile 一致，但 Druid 35.0.0 在 CDN 上已不可用。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（Apache 官方归档站），该站点保留所有历史版本。URL 改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此修复方式与模式01、模式02、模式27、模式38中同类 404 问题的修复策略一致。

### 方向 2（置信度: 中）
若 `archive.apache.org` 在 CI 构建环境中网络不可达，可改用华为云镜像站等国内加速源。需先确认对应镜像站是否托管了 Druid 制品。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实存在（需手动访问确认 Apache 归档站已有该版本）。
- 检查同目录下已有的 SP2 版本的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用了相同的 `dlcdn.apache.org` URL，如果是且其 CI 仍能通过，说明 CDN 下架是近期的，需一并修复 SP2 版本。
- 此外日志中存在一个非致命的 BuildKit 警告 `FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`，建议将 `as` 改为 `AS` 以消除该 lint 警告，但不是本次构建失败的原因。

## 修复验证要求
无需额外验证步骤。将 URL 从 `dlcdn.apache.org` 更换为 `archive.apache.org` 即可修复。code-fixer 在提交前应从浏览器/curl 确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可正常返回 200。
