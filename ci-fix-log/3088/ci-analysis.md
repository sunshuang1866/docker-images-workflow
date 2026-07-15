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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget ...` 步骤）
- 失败原因: `dlcdn.apache.org` CDN 仅保留 Apache Druid 最新版本，druid 35.0.0 的二进制包已被下架（或在 CDN 路径中不可用），wget 收到 HTTP 404 响应。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中下载 URL 使用了 `dlcdn.apache.org` 作为下载源。该 CDN 的行为特性与模式01（Maven）和模式38（ActiveMQ）完全一致——`dlcdn.apache.org` 只托管当前最新版，历史版本下架后返回 404。这是 PR 引入的构建问题，需要修正下载源。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`（Apache 归档镜像），后者保留所有历史版本：

- 原 URL: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 改为: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

这是 Apache 项目处理 CDN 仅保留最新版的通用解决方案（参考模式01、模式38）。

### 方向 2（置信度: 中）
升级 druid VERSION 至最新可用版本。如果 druid 35.0.0 的上一个小版本（如 35.0.1、35.0.2）在 `dlcdn.apache.org` 仍可用，可直接升级版本号。但此方案治标不治本，未来新版本发布后旧版本仍会 404。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在归档站确实存在（archive.apache.org 通常保留所有发布版本，但偶有例外）。
- 确认 `archive.apache.org` 从 CI 构建环境可达（参考模式33，部分 Apache 镜像站可能有网络连通性问题；如需备选，可考虑 `repo.huaweicloud.com` 镜像站）。

## 修复验证要求
若采用方向 1（更换为 `archive.apache.org`），code-fixer 必须：
1. 从 CI 构建环境或本地执行 `wget --spider https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 验证该 URL 可访问。
2. 如果 archive.apache.org 也不可达，尝试华为云镜像站替代：`repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`。
