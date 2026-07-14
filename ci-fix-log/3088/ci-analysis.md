# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式01
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

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
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 上不存在 `apache-druid-35.0.0-bin.tar.gz`，wget 返回 HTTP 404。Apache CDN（dlcdn.apache.org）仅托管当前最新版本的制品，Druid 35.0.0 的二进制包可能已被下架或从未被同步到该 CDN。

### 与 PR 变更的关联
直接由本次 PR 引入。PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行的 `wget` 命令硬编码了从 `dlcdn.apache.org` 下载 Druid 35.0.0 的 URL，该 URL 在构建时返回 404，导致 Docker 构建失败。此问题与模式01（Apache CDN Maven 版本 404）机制相同——`dlcdn.apache.org` 作为 CDN 不会保留所有历史版本。

## 修复方向

### 方向 1（置信度: 中）
将 Druid 二进制包的下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，后者归档了所有 Apache 历史版本。URL 格式为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 低）
改用华为云镜像站作为下载源：
`https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
（需验证该镜像站是否托管了 Druid 35.0.0）

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在并可访问。
- 确认 Apache Druid 35.0.0 的官方二进制发布包文件名确实为 `apache-druid-35.0.0-bin.tar.gz`（而非其他命名格式如 `apache-druid-35.0.0.tar.gz`）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用，本修复为 URL 替换，不涉及正则 patch。）
