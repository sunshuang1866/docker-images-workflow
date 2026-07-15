# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式38（Apache CDN 下载源 404）+ 模式01（Apache CDN 版本 404）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz && tar -zxvf apache-druid-35.0.0-bin.tar.gz && mv apache-druid-35.0.0 /opt/druid && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz && ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（RUN wget 步骤）
- 失败原因: `dlcdn.apache.org` 是 Apache CDN 分发节点，通常只保留最新版本制品，Apache Druid 35.0.0 的历史版本已从该 CDN 节点下架，wget 请求返回 HTTP 404。

### 与 PR 变更的关联
PR 新增的 Dockerfile 将下载源硬编码为 `dlcdn.apache.org/druid/${VERSION}/...`。该 URL 在 CI 构建时（2026-07-10）已返回 404，说明 Apache Druid 35.0.0 已不在 CDN 上。此失败并非 PR 代码逻辑错误，而是下载源选择不当导致——`dlcdn.apache.org` 不适合用于非最新版本的历史版本下载。Druid 35.0.0 的 SP2 版本（`35.0.0-oe2403sp2`）在更早时间点构建时 CDN 可能仍持有该版本，因此当时未触发此问题。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org`，该站点长期保留 Apache 所有历史发行版，不会随时间下架。参考 URL 格式：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

此修复方向与模式01（Maven CDN 404）、模式38（ActiveMQ CDN 404）的解决思路一致——Apache CDN 不保证历史版本可用性，应使用 archive 站点或华为云等镜像站。

## 需要进一步确认的点
- 验证 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实可达（建议 curl -I 确认返回 200 而非 404）。
- 确认 Druid 35.0.0 是否还存在于其他可用镜像源（如 `https://repo.huaweicloud.com/apache/druid/`），以便选择网络连通性最佳的源。

## 修复验证要求
code-fixer 在提交前，需用 `curl -sL -o /dev/null -w "%{http_code}" ` 验证目标下载 URL 返回 HTTP 200（而非 404），确认 archive.apache.org 或替代镜像站确实托管了 Apache Druid 35.0.0 的二进制包。
