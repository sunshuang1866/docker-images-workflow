# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（同类根因：Apache CDN 仅保留最新版本，历史版本被下架后返回 404）
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
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（RUN wget 步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本制品。Druid 35.0.0 的二进制包已被 CDN 节点下架，导致 `wget` 下载时返回 HTTP 404，Docker 构建在 builder 阶段的第 3 步失败（exit code: 8）。

### 与 PR 变更的关联
PR 新增的 Dockerfile `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 在 builder 阶段使用 `wget` 从 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包。该 URL 返回 404 即是本次 CI 失败的直接原因。失败与 PR 新增的 Dockerfile 代码直接相关——下载源选择（`dlcdn.apache.org`）不适合获取历史版本。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 改为 `archive.apache.org`。`archive.apache.org` 是 Apache 官方归档站点，保留所有已发布版本的历史制品。例如将 URL 从：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
若 `archive.apache.org` 在 CI 环境中也存在网络不通问题（参考模式33，`archive.apache.org` 在部分 CI 节点不可达），可使用华为云镜像站等替代源。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建环境中可访问（避免模式33 中 `archive.apache.org` 网络不通的问题）。
- 需要确认 Druid 35.0.0 在 `archive.apache.org` 是否确实存在且有对应制品。

## 修复验证要求
code-fixer 在提交前必须验证 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在当前 CI 构建环境中可通过 `wget` 成功下载（返回 200），确保替换后的 URL 有效。
