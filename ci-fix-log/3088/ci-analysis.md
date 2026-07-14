# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz     && tar -zxvf apache-druid-35.0.0-bin.tar.gz     && mv apache-druid-35.0.0 /opt/druid     && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 0.655
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz     && tar -zxvf apache-druid-${VERSION}-bin.tar.gz     && mv apache-druid-${VERSION} ${DRUID_HOME}     && rm -f apache-druid-${VERSION}-bin.tar.gz" did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（builder 阶段的 `wget` 下载步骤）
- 失败原因: Apache CDN（`dlcdn.apache.org`）对 Druid 35.0.0 的二进制包返回 HTTP 404，该 CDN 采用 pull-through 缓存模型，不会保留所有历史版本的制品。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中下载源直接使用了 `dlcdn.apache.org`（Apache CDN）。该 URL 在当前时刻不持有 Druid 35.0.0 的二进制 tarball，导致构建失败。此问题与已存在的模式01高度一致——Apache CDN 不保证旧版本制品的可得性。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org`（Apache 官方归档站）：
- 当前 URL: `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 建议 URL: `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

Apache Archive 会永久保留所有已发布版本，不存在版本下架问题。

### 方向 2（置信度: 中）
若 `archive.apache.org` 在 CI 环境中不可达（参考模式33），可使用华为云镜像站：
- 备选 URL: `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 或 `repo.huaweicloud.com/apache/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 在 CI 构建网络中可达且文件存在。
- 确认 SP2 版本的 Druid Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）是否也使用了相同的 `dlcdn.apache.org` 源——如果是，说明该版本在之前构建时 CDN 尚未清除，属于时效性触发；应一并评估 SP2 是否需要同步修复。

## 修复验证要求
- code-fixer 在提交前，需手动 wget 验证所选替代 URL 能成功下载 Druid 35.0.0 的二进制包（HTTP 200 + 文件为有效的 tar.gz）。
- 若选用 `archive.apache.org`，需确认 CI 构建网络能正常访问该域名（部分 CI 环境中 `archive.apache.org` 曾出现过不可达，参考模式33）。
