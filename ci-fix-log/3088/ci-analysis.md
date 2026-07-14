# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN 版本 404），同根参考：模式38（ActiveMQ 下载源 404）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` CDN 只托管最新版本的 Apache 项目制品，Apache Druid 35.0.0 的二进制包已从该 CDN 下架，`wget` 请求返回 HTTP 404。

### 与 PR 变更的关联
PR #3088 新增的 Dockerfile 使用 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 作为下载源。这是导致本次失败的直接原因——PR 引入了一个对新镜像不可用的下载 URL。Druid 35.0.0 本身是一个已存在且有效的版本（已在 openEuler 24.03-LTS-SP2 上支持），问题仅在于 CDN 分发节点不再保留该历史版本。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org`，后者保留所有 Apache 项目的历史版本归档。

URL 格式参考：
- 当前（404）: `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`
- 归档: `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`

此方向与历史模式01（Maven CDN 404）和模式38（ActiveMQ CDN 404）的修复方法一致，验证路径清晰。

### 方向 2（置信度: 中）
将下载源替换为国内镜像站（如 `repo.huaweicloud.com/apache/druid/`），前提是该镜像站提供 Druid 35.0.0 的制品。需先确认镜像站是否托管该版本。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在且可访问（归档站应保留所有历史版本）。
- 确认 Apache Druid 35.0.0 在 `archive.apache.org` 上的确切路径结构（`/dist/druid/` 还是 `/dist/druid/35.0.0/`）。

## 修复验证要求
- code-fixer 在提交前，必须验证替换后的下载 URL（如 `archive.apache.org` 路径）确实可访问且返回有效的 tar.gz 文件。可通过 `wget --spider` 或浏览器直接访问目标 URL 确认 HTTP 200 响应，而非仅凭格式推断。
