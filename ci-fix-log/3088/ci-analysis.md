# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01（相似）
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
- 失败原因: Apache CDN (`dlcdn.apache.org`) 已移除 Druid 35.0.0 的二进制包，wget 请求返回 404 Not Found。与模式01（Apache CDN Maven 版本 404）根因一致 — `dlcdn.apache.org` 仅保留各项目最新版本，旧版本制品会被下架。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其第 9 行使用 `dlcdn.apache.org` 作为下载源。在 PR 合入时，Druid 35.0.0 已从该 CDN 被移除，导致构建直接失败。该失败由 PR 变更直接触发（新增 Dockerfile 引用了已失效的下载 URL）。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 Apache Archive（`https://archive.apache.org/dist/druid/`），后者保留所有历史版本不会下架。参考已有历史案例（模式01 中 Maven 换源到 `archive.apache.org`），Druid 也可用同样方式解决。

### 方向 2（置信度: 中）
将下载源切换为华为云镜像站（如 `https://repo.huaweicloud.com/apache/druid/`），前提是该镜像站保留了 Druid 35.0.0 制品。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或 `https://repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 上该版本制品确实存在并可正常下载。
- 确认 Druid 35.0.0 的上游最新版本是否已变化 — 如果已有新版本（如 35.0.1），需要考虑是否有必要保持版本号不变。

## 修复验证要求
code-fixer 在提交前，必须用 `wget --spider` 或 `curl -I` 验证新的下载 URL 确实返回 HTTP 200，确认替换后的源上有 Druid 35.0.0 制品可用。
