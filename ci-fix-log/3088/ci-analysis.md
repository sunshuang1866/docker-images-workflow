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
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（builder 阶段的 wget 下载指令）
- 失败原因: Apache Druid 35.0.0 的二进制包在 `dlcdn.apache.org` CDN 上已不存在（返回 HTTP 404）。与模式01（Maven CDN 404）和模式38（ActiveMQ CDN 404）同根同源——`dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，历史版本的制品会从 CDN 下架。

### 与 PR 变更的关联
本次 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中 builder 阶段通过 `wget` 从 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包。该下载源对 35.0.0 版本返回 404，直接导致 Docker 构建在 builder 阶段失败。此问题是 PR 新增 Dockerfile 引入的下载源选择不当所致。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/druid/`（Apache 归档站保留所有历史版本，不会下架）。URL 构造为：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

### 方向 2（置信度: 中）
将下载源替换为华为云镜像站（如模式01中 Maven 的修复方式），例如：
```
https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
需要注意镜像站是否收录了 Druid 35.0.0 版本，若未收录则可能同样返回 404。

## 需要进一步确认的点
- 确认 Apache Druid 35.0.0 在 `archive.apache.org` 上的实际路径是否与方向1中假设的一致（可尝试在 Docker 构建环境外手动 `wget --spider` 验证）。
- 确认同仓库中已存在的 Druid 35.0.0-oe2403sp2 版本（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）使用的下载源是什么——如果该版本使用了不同的源（如 archive）且仍能构建成功，则方向1的高置信度可得到进一步确认。

## 修复验证要求
- 修复前，从 Apache 归档站或镜像站验证 Druid 35.0.0 二进制包的下载可用性（`wget --spider` 或 `curl -I`），确保替换后的 URL 确实返回 HTTP 200。
