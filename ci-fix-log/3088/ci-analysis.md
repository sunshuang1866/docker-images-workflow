# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式02
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
------
Dockerfile:9
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
------
ERROR: failed to solve: process "... did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Docker 构建时 wget 请求 `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，Apache CDN（dlcdn.apache.org）上不存在 Apache Druid 35.0.0 的二进制包。

### 与 PR 变更的关联
本次 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中在 builder 阶段（第 9 行）硬编码了 `dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 作为下载源。该 URL 在 Apache CDN 上不可用（404），导致 Docker 构建在下载步骤直接失败。此失败由 PR 引入的 Dockerfile 直接触发。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/druid/`（Apache 归档站保留所有历史版本），URL 模式为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。这是模式01/02/38 同类问题的标准修复方案。

### 方向 2（置信度: 中）
换用国内镜像站（如华为云 `repo.huaweicloud.com/apache/druid/`）下载，适用于 CI 构建环境访问 `archive.apache.org` 不可达的场景。需先验证华为云镜像站上确有 Druid 35.0.0 的二进制包后再替换。

## 需要进一步确认的点
- **验证版本存在性**：确认 Apache Druid 35.0.0 是否为已发布的正式版本。若该版本尚未发布或压根不存在，则需要改用实际可用的版本号。
- **验证 archive.apache.org 可达性**：如 CI 环境的模式33 历史案例所示，`archive.apache.org` 可能在某些构建节点上不可达。修复前需确认目标替换 URL 在当前 CI 环境中可访问。
- **确认 CNCF 领域的 Druid 包是否在华为云镜像站有同步**：若华为云镜像站没有 Druid 35.0.0 的制品，则应优先使用 `archive.apache.org`。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本失败为下载源 URL 替换，不涉及正则 patch。）
