# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式38（Apache CDN 下载源 404，同类模式：模式01、模式33）
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
------
ERROR: failed to solve: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget ...` 步骤）
- 失败原因: Dockerfile 中使用的下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。Apache Druid 35.0.0 的二进制发行包在 `dlcdn.apache.org` CDN 上不可用（该 CDN 不托管 Druid 或已移除该版本）。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中直接使用 `dlcdn.apache.org` 作为 Apache Druid 35.0.0 二进制包的下载源。该 URL 在 CI 构建环境中返回 404，是本次 PR 变更直接导致的失败。同一 Druid 35.0.0 版本的已有 SP2 Dockerfile 可能使用了不同的下载源（如 `archive.apache.org` 或华为云镜像站）因而构建成功。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 二进制包的下载源从 `dlcdn.apache.org` 更换为其他可用源：
- `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（Apache 归档站，保隆历史版本）
- `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（华为云镜像站，CI 环境中已验证可用）
- `https://downloads.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（Apache 主下载站）

参考同仓库中已有的 Druid 35.0.0 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）的下载 URL，保持一致性。

### 方向 2（置信度: 中）
如果 Druid 35.0.0 在 Apache 所有官方下载源中均不存在，则 URL 路径格式可能有误（如包名或目录结构与实际发布不一致），需要直接访问 Apache Druid 官方下载页面确认 35.0.0 版本的实际下载路径和文件命名。

## 需要进一步确认的点
1. 同版本已有 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）使用的下载 URL 是什么，与本次 PR 新增的 SP4 Dockerfile 是否一致
2. Apache Druid 35.0.0 在 `archive.apache.org`、`downloads.apache.org` 或华为云镜像站上是否真实存在且可下载

## 修复验证要求
code-fixer 在提交前，需实际执行 `wget`（或 `curl -I`）验证新 URL 确实返回 HTTP 200，确认 Apache Druid 35.0.0 二进制包在目标源上可下载后再提交。
