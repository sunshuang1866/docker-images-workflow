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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`（wget 下载步骤）
- 失败原因: `dlcdn.apache.org` 对 Druid 35.0.0 的二进制包 `apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。Apache CDN（dlcdn）遵循与 Maven 类似的策略，仅保留最新若干版本，旧/特定版本下架后返回 404。

### 与 PR 变更的关联
PR 新增的 Dockerfile 将下载源设为 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，其中 `VERSION=35.0.0`。该版本在 `dlcdn.apache.org` 上已不可用，直接导致构建失败。此失败完全由本次 PR 新增的 Dockerfile 引起。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 换为 `archive.apache.org/dist/druid`，Apache 归档站保留所有历史版本，不受 CDN 下架影响：
```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```
此方案与模式01和模式02中多处历史修复一致（如 PR #1932 phoenix、PR #2267 haproxy 等），从 CDN 切换到 archive 归档站。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 同样不可达（参考模式33中 `downloads.apache.org` 网络不通的历史案例），可将下载源替换为华为云镜像站或其他国内可达镜像：
```
https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

## 需要进一步确认的点
- 验证 Druid 35.0.0 在 `archive.apache.org/dist/druid/35.0.0/` 目录下确实存在 `apache-druid-35.0.0-bin.tar.gz`
- 确认同一版本已有的 `35.0.0-oe2403sp2` Dockerfile 是否使用相同下载源（若 SP2 仍可构建，需对比其下载 URL 是否已采用 archive 镜像站）
- 若 archive.apache.org 也无法连接到 CI 构建环境，需要先验证网络可达性

## 修复验证要求
- code-fixer 在提交前，需手动验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`（或所选替代 URL）确实可访问且返回 200
- 若替换为华为云镜像站或其他镜像源，同样需确认对应 URL 返回 200 后再提交
