# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38
- 新模式标题: (不适用 — 已有模式覆盖)
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
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（RUN wget 步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只托管当前最新版本。Apache Druid 35.0.0 已从该 CDN 下架，导致 `wget` 访问 `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。此根因与**模式01**（Maven CDN 404）和**模式38**（ActiveMQ CDN 404）完全相同——均因 Apache CDN 不保留历史版本导致。

### 与 PR 变更的关联
PR 新增的 Dockerfile `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 在第 9 行使用 `wget` 从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0，该版本在 CDN 上已不可用。这是 PR 改动直接触发的失败。

附加信息：日志中有一个非致命的 BuildKit 警告 `FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`，指 Dockerfile 第 3 行 `FROM ${BASE} as builder` 中的 `as` 应写为 `AS`（大写）。这不影响构建结果，但建议修复。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（CDN，仅保留最新版）替换为 `archive.apache.org`（归档站，保留历史版本）。目标 URL 格式为：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
`archive.apache.org` 是 Apache 官方归档站，历史上所有已发布版本均会迁移至此。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 构建环境中网络不可达（参考模式33），可改用华为云镜像站 `repo.huaweicloud.com` 的 Apache 镜像，前提是该镜像站保留了 Druid 35.0.0 的制品。

## 需要进一步确认的点
无。日志清晰，根因明确。

## 修复验证要求
无需特别验证步骤。修复方向仅涉及将 `dlcdn.apache.org` 替换为 `archive.apache.org`，不涉及正则 patch 外部源文件。
