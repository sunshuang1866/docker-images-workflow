# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38（Apache CDN 历史版本 404，同类问题涉及 Maven、ActiveMQ）
- 新模式标题: (无需)
- 新模式症状关键词: (无需)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz     && tar -zxvf apache-druid-35.0.0-bin.tar.gz     && mv apache-druid-35.0.0 /opt/druid     && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
------
Dockerfile:9
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9（wget 下载步骤）
- 失败原因: `dlcdn.apache.org` CDN 上不存在 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`，返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，旧版本下架后返回 404。Dockerfile 中直接使用 `dlcdn.apache.org` 作为下载源导致历史版本 Druid 35.0.0 无法下载，wget 返回 exit code 8，Docker 构建失败。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行 wget 命令将下载源硬编码为 `dlcdn.apache.org`。该 URL 在 Docker 构建时返回 404，直接导致构建失败。这是该 Dockerfile 自身的下载源选择问题，与 README.md、image-info.yml、meta.yml 的变更无关。已存在的 SP2 版本（`35.0.0-oe2403sp2`）若也使用相同 URL 且当时能成功下载，说明 Apache CDN 在 SP2 构建之后下架了该版本，与知识库中模式 01（Maven）、模式 38（ActiveMQ）的根因一致。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/druid/`。Apache 归档站（`archive.apache.org`）完整保留所有历史版本，不受 CDN 下架影响。URL 格式变更：
- 当前: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 改为: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
如果 `archive.apache.org` 在 CI 构建环境中同样不可达（参考模式 33 中 `archive.apache.org` 曾在某些构建节点网络不通），可换用华为云镜像站 `repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`（需确认该镜像站同步了 Druid 35.0.0）。

## 需要进一步确认的点
- 已存在的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）的下载源是什么——如果也是 `dlcdn.apache.org`，则说明 CDN 确实在两次构建之间下架了 35.0.0，修复方向 1 正确；如果 SP2 用的是其他源（如 archive），则应直接参照 SP2 的方案。

## 修复验证要求
- code-fixer 必须使用 wget 或 curl 在修复后验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 实际可下载（返回 HTTP 200），确认归档站确实托管了该版本的 Druid 二进制包后再提交。
