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
------
Dockerfile:9
--------------------
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（wget 下载步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留各项目的最新版本，历史版本（此处为 Apache Druid 35.0.0）已从 CDN 下架，导致 `wget` 请求返回 HTTP 404。

### 与 PR 变更的关联
PR 新增的 Dockerfile 直接使用 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。该 URL 在 PR 提交时可能有效，但 Apache CDN 在 Druid 发布新版本后已将 35.0.0 制品下架。这是 PR 代码引入的选择（使用 CDN 而非归档源）直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（不保留历史版本）更换为 `archive.apache.org/dist/druid/`（Apache 归档站，保留所有历史版本），URL 模板改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此方案与模式01、模式38 的修复思路一致：`archive.apache.org` 长期保留历史发布制品。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 网络不可达（参考模式33），可尝试使用其他镜像站（如华为云镜像 `repo.huaweicloud.com/apache/druid/`）或升级 Druid 版本到 CDN 当前可用的最新版。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可访问（Apache 归档站应保留该文件）。
- 确认 CI 构建环境能否正常访问 `archive.apache.org`（参考模式33 中 `archive.apache.org` 可能存在网络不通问题，若不通则需换华为云镜像站）。

## 修复验证要求
code-fixer 在提交前，需验证 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 实际可下载（wget 测试返回 200），若不可达则回退到华为云镜像源 `repo.huaweicloud.com`。
