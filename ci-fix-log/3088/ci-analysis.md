# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（同类根因，跨包重现）
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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本制品。Druid 35.0.0 的二进制包 `apache-druid-35.0.0-bin.tar.gz` 已从该 CDN 下架，wget 请求返回 HTTP 404。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 的 Dockerfile，其中 **Dockerfile:9** 的 wget 下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是本次新增的代码。该 URL 在 CDN 上不可用，直接导致 Docker 构建失败。与 PR 代码改动**强相关**。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`。Apache Archive 长期保留所有历史版本制品，不会随新版本发布而下架旧版本。参考已通过 CI 验证的模式01/模式38 修复案例，将 URL 从：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
若 `archive.apache.org` 同样不可达（参考模式33 中 `downloads.apache.org` 和 `archive.apache.org` 的网络连通性问题），可改用华为云镜像站或清华镜像站等国内可访问的 Apache 镜像源。

## 需要进一步确认的点
1. 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实存在且可下载。
2. 确认 Druid 35.0.0 是否为 Apache 官方发布的正式版本（非 RC/alpha/beta），若版本号本身有误，可能需要更正 VERSION 值。
3. 参照同仓库中已有的 Druid 35.0.0-oe2403sp2 Dockerfile，确认该版本在 SP2 上是否已验证过相同下载源可用。

## 修复验证要求
code-fixer 在提交修复前，需用 `curl -I` 或 `wget --spider` 验证新下载 URL 返回 HTTP 200（非 404/403/超时），确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 路径下制品存在且可达。
