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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz \
    && tar -zxvf apache-druid-35.0.0-bin.tar.gz \
    && mv apache-druid-35.0.0 /opt/druid \
    && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget` 步骤）
- 失败原因: Dockerfile 从 `dlcdn.apache.org` CDN 下载 Apache Druid 35.0.0 二进制包时返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发前端，通常只保留最新版本，历史版本（包括 35.0.0）已被下架删除。这与历史模式01（Apache CDN Maven 版本 404）的根因完全一致——Apache CDN 不保证历史版本制品的持久可用性。

### 与 PR 变更的关联
PR 新增的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`）第 9 行直接使用了 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。同一版本在已有的 SP2 Dockerfile 中可能曾经可用，但 CDN 在 SP4 Dockerfile 提交后（构建时）已不再托管该版本，导致构建失败。问题由本次 PR 的 Dockerfile 新增直接触发。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为可长期保留历史版本的上游源：
- **Apache Archive**: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` — Apache 官方归档站，保留所有发布版本
- **华为云镜像站**: `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` — 已验证在 CI 环境中网络可达且保留历史版本（参考模式01/33中的历史案例）

### 方向 2（可选，置信度: 中）
若 Druid 35.0.0 确实在所有上游源中均不存在（需验证），则需检查上游 Apache Druid 项目是否已撤回该版本，考虑升级到 CDN 当前可用版本。

## 需要进一步确认的点
1. 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否存在（Apache 归档站应保留所有已发布版本）
2. 确认已有的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用相同 CDN 源，若同样指向 `dlcdn.apache.org`，则该 SP2 镜像的后续重建也会面临相同失败
3. 验证华为云镜像站 `repo.huaweicloud.com/apache/druid/35.0.0/` 路径下是否有对应制品

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次修复为更换下载 URL，不涉及正则 patch 外部源文件）
