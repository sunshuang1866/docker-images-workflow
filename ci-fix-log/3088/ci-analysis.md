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
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9
- 失败原因: `dlcdn.apache.org` 上不存在 `apache-druid-35.0.0-bin.tar.gz`（返回 HTTP 404）

### 与 PR 变更的关联
PR 新增的 Dockerfile 使用 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 下载 Druid 35.0.0 二进制包。Apache CDN（dlcdn.apache.org）通常只托管最新版本，Druid 35.0.0 的制品可能已从该 CDN 下架，导致 wget 返回 404 并构建失败。这与**模式01**（Apache CDN Maven 版本 404）机理完全一致——Apache CDN 淘汰旧版本后，直接下载 URL 返回 404。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，后者完整保留 Apache 项目所有历史发布版本的制品。URL 格式为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
若 CI 环境中 `archive.apache.org` 网络不可达（参考模式33），可换用第三方 Apache 镜像站，如 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/` 目录下确实存在 `apache-druid-35.0.0-bin.tar.gz` 文件
- 确认现有 `35.0.0-oe2403sp2` 的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否使用相同下载源——如果同样指向 `dlcdn.apache.org`，则 SP2 构建在当前时间可能也已失败
- 在 CI 环境中测试替代镜像站的可达性

## 修复验证要求
code-fixer 必须在提交前验证所选替代下载源上确实存在 Druid 35.0.0 的二进制包：用 `wget --spider` 或 `curl -I` 检查 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 200。若 archive.apache.org 不可用，则需在 CI 构建环境中实际测试第三方镜像站的下载可达性（参考模式33中 `repo.huaweicloud.com` 作为已验证可靠的替代源）。
