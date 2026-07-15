# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式38（Apache CDN 404 → ActiveMQ）/ 模式01（Apache CDN Maven 版本 404）
- 新模式标题: (不适用)

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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`（wget 下载步骤）
- 失败原因: Apache Druid 35.0.0 的二进制压缩包 `apache-druid-35.0.0-bin.tar.gz` 在 `dlcdn.apache.org` CDN 上返回 HTTP 404。与 `模式38`（ActiveMQ CDN 404）和 `模式01`（Maven CDN 404）同根——`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，不保证历史版本的可用性。

### 与 PR 变更的关联
PR 新增的 Dockerfile 直接使用了 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源，该 URL 在 `VERSION=35.0.0` 时不可达，构建失败。失败与 PR 变更直接相关。

## 修复方向

### 方向 1（置信度: 高）
将 Apache Druid 的下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 归档站，保留历史版本）或 `repo.huaweicloud.com`（华为云镜像站）。例如将 URL 从：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
改为 `archive.apache.org` 对应的归档路径。

### 方向 2（置信度: 中）
升级 VERSION 到 `dlcdn.apache.org` 上当前实际可用的最新 Druid 版本（如存在更新的 35.x 版本）。但考虑到 Dockerfile 明确选择了 35.0.0 且有同系列的 35.0.0-oe2403sp2 已存在，方向 1（换归档源）更合理。

## 需要进一步确认的点
- 确认 Apache Druid 35.0.0 在 `archive.apache.org` 上的实际路径（如 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`）
- 参考同仓库中已有的 Druid 35.0.0-oe2403sp2 Dockerfile，确认其下载源是否也使用了类似 URL（如果 SP2 版本构建成功，可能是 CDN 在 SP4 构建期间才下架了该版本）

## 修复验证要求
code-fixer 必须通过 `curl -I` 或 `wget --spider` 验证新的下载 URL 在构建环境中确实可访问（返回 200），不能仅假设 `archive.apache.org` 路径一定存在。若 `archive.apache.org` 同样不可达，可尝试华为云镜像站 `repo.huaweicloud.com/apache/druid/`。
