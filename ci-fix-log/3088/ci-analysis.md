# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404）
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

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
------
Dockerfile:9
--------------------
   9 | >>> RUN wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz \
  10 | >>>     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz \
  11 | >>>     && mv apache-druid-${VERSION} ${DRUID_HOME} \
  12 | >>>     && rm -f apache-druid-${VERSION}-bin.tar.gz
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`
- 失败原因: `dlcdn.apache.org` 是 Apache CDN，通常仅保留最新版本，历史版本下架后返回 404。Dockerfile 中构造的下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在该 CDN 上不存在（HTTP 404）。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中下载源使用了 `dlcdn.apache.org`。该 CDN 不保证历史版本持久可访问，导致 druid 35.0.0 的二进制包下载失败。这是 PR 引入的 URL 选择问题——应使用能稳定保留历史版本的下载源。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org`，归档站保留所有历史发布版本：
- 原 URL: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 归档 URL: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

参考历史案例中模式01（Maven CDN 404）和模式38（ActiveMQ CDN 404）的处理方式——均通过切换为归档站或其他镜像站解决问题。

### 方向 2（置信度: 中）
若 `archive.apache.org` 也不可用（参见模式33——CI 环境中 `archive.apache.org` 网络不可达的历史案例），可改用华为云镜像站：
- `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 需要进一步确认的点
1. 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实存在该二进制包（Apache Druid 35.0.0 可能尚未在归档站发布，或文件名/路径格式不同）。
2. 如归档站也不可用，检查 Apache Druid 官方发布页面确认 35.0.0 的实际下载 URL 格式。
3. 参考同版本已有的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`），确认其使用的下载源和 URL 是否正确，SP4 可直接复用已验证的 URL。

## 修复验证要求
code-fixer 在提交前，必须：
1. 从浏览器或 curl 直接访问 `https://archive.apache.org/dist/druid/35.0.0/` 目录，确认 `apache-druid-35.0.0-bin.tar.gz` 文件存在且文件名完全匹配。
2. 若归档站不存在该文件，尝试访问 `https://dlcdn.apache.org/druid/` 查看当前 CDN 上实际托管了哪些版本，确认 35.0.0 是否需要换用其他下载源（如华为云镜像 `repo.huaweicloud.com`）。
