# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式01
- 新模式标题: (无)
- 新模式症状关键词: (无)

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
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: Apache CDN (`dlcdn.apache.org`) 对 `druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，Druid 35.0.0 二进制包已从 CDN 下架（Apache CDN 只保留最新版本）

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其下载 URL 使用的 `dlcdn.apache.org` 托管策略为仅保留当前最新版本，Druid 35.0.0 可能已被更新版本取代而移除。该问题与 SP4 平台本身无关，同一下载 URL 在 SP2 的 Dockerfile 中若此时重新构建也会失败。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`，后者保留所有历史版本：

```
https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz
```

### 方向 2（置信度: 中）
使用国内镜像站（如华为云 `repo.huaweicloud.com/apache/druid/`），可能在 CDN 失效期间仍缓存了该版本，且可加速国内 CI 构建下载速度。

## 需要进一步确认的点

1. 确认 Apache Druid 35.0.0 在 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在
2. 检查现有 SP2 的 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用相同的 `dlcdn.apache.org` 下载源——如果是，则该 Dockerfile 也需要一并修复

## 修复验证要求

code-fixer 必须在提交前，用 `wget --spider` 或 `curl -I` 验证新下载 URL 返回 HTTP 200/301/302，确保目标文件确实存在于替换后的源上。
