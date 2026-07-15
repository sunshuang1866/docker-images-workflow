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
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（wget 下载步骤）
- 失败原因: `dlcdn.apache.org` CDN 不再托管 Druid 35.0.0 的二进制包 `apache-druid-35.0.0-bin.tar.gz`，返回 HTTP 404。与模式01中 Maven 的问题同根同源——`dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留当前最新版本，历史版本下架后返回 404。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行使用 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包。该 URL 在 PR 提交时可能短暂可用，但 CDN 已下架此版本，导致构建失败。这是 PR 变更直接引发的失败——若换用可永久访问的归档源，构建即可通过。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org`（Apache 官方归档站，保留所有历史版本），URL 格式：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

按模式01和模式33的历史案例，`archive.apache.org` 有时也可能不可达（取决于 CI 构建环境），若遇到超时，可备选华为云镜像站 `repo.huaweicloud.com`。

### 方向 2（置信度: 中）
升级 Druid 版本至 CDN 当前托管的最新版本（若能找到当前可用版本号）。但考虑到 `35.0.0` 是 SP4 的目标版本，升级会改变镜像内容，优先采用方向 1。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否实际可访问
- 检查同项目的已有 SP2 Dockerfile (`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`) 使用的是什么下载源，作为参考

## 修复验证要求
code-fixer 必须从 `archive.apache.org` 或 `repo.huaweicloud.com` 验证 `apache-druid-35.0.0-bin.tar.gz` 确实存在且可下载，确认 URL 可达后再提交修改。若目标归档站不可达，需测试备选镜像站。
