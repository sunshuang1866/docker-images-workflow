# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式01
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
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`（builder 阶段 wget 下载步骤）
- 失败原因: Apache CDN（`dlcdn.apache.org`）上不存在 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`，返回 HTTP 404。`dlcdn.apache.org` 作为 CDN 分发节点通常只保留最新版本，历史或未发布版本不保证可用。

### 与 PR 变更的关联
**PR 变更直接触发**。该 PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中 builder 阶段 `RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 是本次新增代码。`VERSION=35.0.0` 版本在 Apache CDN 上不可用（返回 404），导致 Docker 构建在 builder 阶段第 3/3 步失败。

注：`meta.yml` 中已存在 `35.0.0-oe2403sp2` 条目（指向 `35.0.0/24.03-lts-sp2/Dockerfile`），说明 druid 35.0.0 版本此前曾通过 SP2 Dockerfile 构建，需确认 SP2 的下载源是否也使用 `dlcdn.apache.org`，以及该版本是否已从 CDN 下架。

## 修复方向

### 方向 1（置信度: 中）
将下载源从 Apache CDN（`dlcdn.apache.org`）切换为 Apache 归档站（`archive.apache.org`），后者保留所有历史发行版。URL 格式为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 低）
若 Apache Druid 35.0.0 版本本身不存在于任何 Apache 源（包括归档站），则需将 `VERSION` 降级为 Apache 已实际发布的可用版本。

## 需要进一步确认的点
1. Apache Druid 35.0.0 是否为真实已发布的版本——需在 https://archive.apache.org/dist/druid/ 或 https://druid.apache.org/downloads.html 验证该版本是否存在。
2. `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`（SP2）使用了哪个下载源——若 SP2 也使用 `dlcdn.apache.org` 且曾构建成功，说明该版本已从 CDN 下架，方向 1 成立；若 SP2 使用 `archive.apache.org`，则 SP4 应直接复用相同下载源。

## 修复验证要求
1. code-fixer 必须先在浏览器或 `curl` 中验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否返回 200，确认归档站上有该版本后再修改 Dockerfile。
2. 确认 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）中的下载 URL，确保 SP4 与 SP2 的下载源选择策略一致。
3. 若归档站也无 35.0.0 版本，需在 Apache Druid 官方发布页确认最新可用版本号后调整 `VERSION`。
