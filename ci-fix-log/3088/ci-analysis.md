# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 404，本次为 Druid 实例）
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
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget` 步骤）
- 失败原因: `dlcdn.apache.org`（Apache CDN 分发节点）对 Druid 35.0.0 的二进制包 `apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。这与知识库中模式01（Maven CDN 404）和模式38（ActiveMQ CDN 404）属于同一根因：Apache CDN 仅保留最新版本，历史版本被下架后不可用。

### 与 PR 变更的关联
强关联。本次 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中 wget 下载源直接使用了 `dlcdn.apache.org`。该下载源不保留历史版本，导致构建时 Druid 35.0.0 的二进制包 404，构建失败。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/druid/`（Apache 归档站，永久保留所有历史版本）。URL 模板从 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 构建环境中也不可达（参考模式33，`archive.apache.org`/`downloads.apache.org` 曾出现网络超时），可改用华为云镜像站 `repo.huaweicloud.com/apache/druid/` 作为替代下载源。需确认该镜像站是否同步了 Druid 35.0.0 的制品。

## 需要进一步确认的点
- `archive.apache.org/dist/druid/35.0.0/` 路径下是否存在 `apache-druid-35.0.0-bin.tar.gz`（需手动访问 Apache 归档站验证文件路径和文件名是否完全匹配）
- CI 构建环境是否能正常访问 `archive.apache.org`（参考模式33的历史案例，该域名在部分 CI runner 上可能不可达）

## 修复验证要求
- 修复后需在实际构建环境中验证 Docker 镜像能完整构建成功（包括 x86_64 和 aarch64 两个架构的构建流水线）
- 如果切换到 `archive.apache.org`，需确认该域名在 CI runner（`ecs-build-docker-x86-03-sp`）的网络环境中可达
