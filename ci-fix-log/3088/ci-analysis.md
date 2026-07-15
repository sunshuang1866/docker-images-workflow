# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38（同类根因）
- 新模式标题: (不适用，已有模式覆盖)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9（新增文件中的 wget 行）
- 失败原因: Apache Druid 35.0.0 的二进制包在 `dlcdn.apache.org` 上返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常仅保留最新版本，不保证历史版本的持久可用性（与模式01中 Maven 在 dlcdn 上 404、模式38中 ActiveMQ 在 dlcdn 上 404 的根因完全相同）。

### 与 PR 变更的关联
**直接关联**。PR #3088 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，该文件第 9 行硬编码了从 `dlcdn.apache.org` 下载 Druid 35.0.0 的 wget 命令。`dlcdn.apache.org` 当前已不托管该版本制品，直接导致 Docker 构建在 builder 阶段的第 3/3 步失败。所有其他文件（README.md、image-info.yml、meta.yml）的变更均为配套的元数据更新，与构建失败无关。

## 修复方向

### 方向 1（置信度: 高）
将 Apache Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（Apache 归档站，保留所有历史版本）。修改 `Dockerfile:9` 行的 wget URL：

```
原: https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
改: https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
```

此修复思路与模式01（Maven CDN 404 → 换 archive）、模式38（ActiveMQ CDN 404 → 换 archive）、模式33（网络不通 → 换源）一致。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建环境中确实可达（archive.apache.org 在历史案例中有过不通的记录，见模式33，若不通可备选华为云镜像站 `repo.huaweicloud.com`）。
- 确认 Apache Druid 35.0.0 确实已正式发布在 archive.apache.org 上（若该版本尚未发布或被撤回，需降级到可用版本）。

## 修复验证要求
- code-fixer 必须验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可访问（HTTP 200），确认 Apache Druid 35.0.0 制品确实存在。若无法访问，需检查上游是否有此版本，或改用其他可用镜像源（如华为云镜像站 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）。
