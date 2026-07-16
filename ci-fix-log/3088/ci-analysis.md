# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式（根因链条与 模式01、模式38 相同——Apache CDN 旧版本下架 404）
- 新模式标题: Apache CDN 旧版本 404
- 新模式症状关键词: dlcdn.apache.org, 404 Not Found, druid, wget, exit code: 8

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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，仅保留最新版本。Druid 35.0.0 已从该 CDN 下架，wget 请求返回 HTTP 404，导致 Docker 构建在 `builder` 阶段失败。

### 与 PR 变更的关联
PR 新增的 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 在第 9 行使用 `dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。这是唯一的新增 Dockerfile，失败由该下载 URL 不可用直接触发。DNS 解析和 HTTPS 连接均成功，问题确为服务端 404（资源不存在），排除网络/基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（CDN，仅保最新版）更换为 `archive.apache.org`（归档站，保留历史版本）。将 URL 改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此为 Apache 项目的通用历史版本归档地址，与模式01（Maven）、模式38（ActiveMQ）的修复方式一致。

### 方向 2（置信度: 中）
如果 `archive.apache.org` 也不可用（参考模式33中部分 Apache 归档站在 CI 环境中网络不通的案例），可改用华为云镜像站：
`https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 需要进一步确认的点
1. 确认 Apache Druid 35.0.0 在 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在（归档站通常保留所有正式发布版本，但需验证）。
2. 确认 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`（已有 SP2 版本的 Druid 35.0.0）使用的是什么下载源——如果 SP2 版本能构建成功且使用了非 CDN 源，应直接复用其下载源 URL。
