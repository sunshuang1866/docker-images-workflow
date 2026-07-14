# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（变体）
- 新模式标题: —
- 新模式症状关键词: —

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz \
    && tar -zxvf apache-druid-35.0.0-bin.tar.gz \
    && mv apache-druid-35.0.0 /opt/druid \
    && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
------
Dockerfile:9
--------------------
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
--------------------
ERROR: failed to solve: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache Druid 35.0.0 在 `dlcdn.apache.org` CDN 上已不可用，`wget` 下载返回 HTTP 404。`dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本，不保证历史版本（如 35.0.0）的持续可用性。

### 与 PR 变更的关联
PR 新增的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`）中，构建阶段（builder）从 `dlcdn.apache.org/druid/35.0.0/` 下载二进制包。该 URL 在 CI 构建时刻返回 404，直接导致构建失败。此失败由 PR 变更直接触发。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 Apache 归档站 `archive.apache.org`。Apache Archive 保留所有历史发布版本，不受 CDN 版本清理策略影响。URL 格式为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
换用国内镜像站（如 `repo.huaweicloud.com/apache/druid/`），前提是该镜像站托管了 Druid 35.0.0 版本。需先在 CI 环境或浏览器中验证该镜像站 URL 是否可访问（返回 200），再决定是否使用。

## 需要进一步确认的点
无。日志中错误信息明确，根因清晰。

## 修复验证要求
无。无需验证正则匹配或外部源文件。
