# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（变体）
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
------
ERROR: failed to solve: ... did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9
- 失败原因: `dlcdn.apache.org` 仅托管当前最新版本的 Apache 项目制品，Druid 35.0.0 的二进制包已从该 CDN 下架，导致 `wget` 下载时返回 HTTP 404。

### 与 PR 变更的关联
**PR 直接触发**。PR 新增的 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 使用 `dlcdn.apache.org` 作为下载源，该 CDN 不保留历史版本，导致 `wget` 请求 `apache-druid-35.0.0-bin.tar.gz` 时返回 404。此问题与历史模式01（Apache CDN Maven 版本 404）完全同源——都是 `dlcdn.apache.org` 清理旧版本制品后导致下载失败。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 的下载源从 `dlcdn.apache.org` 切换至 `archive.apache.org`。`archive.apache.org` 保留所有 Apache 项目的历史 release 制品，对应 URL 格式为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。此修复方法在历史模式01、模式27 中已验证有效。

### 方向 2（置信度: 中）
若 `archive.apache.org` 网络不可达（参考模式33 中 `downloads.apache.org` 超时问题），可改用华为云等国内镜像站作为备用下载源。

## 需要进一步确认的点
- 建议在修复前通过 `curl -I` 直接验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实可访问（返回 200），确保目标文件存在于 archive 中。
- 确认同一版本的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）使用的是什么下载源，如果 SP2 版本也已失效，也需一并修复。

## 修复验证要求
code-fixer 必须：
1. 在修复前，通过 `curl -I https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确认目标文件在 Apache Archive 中存在（HTTP 200）。
2. 若 Apache Archive 不可达，验证其他镜像源（如华为云）该文件的可达性后再提交。
