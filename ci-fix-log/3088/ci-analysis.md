# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式38
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz ...
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9（builder 阶段 wget 下载命令）
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，不保证历史版本的可用性。Dockerfile 中构造的下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，Apache Druid 35.0.0 的二进制包在该 CDN 上已不可用。

### 与 PR 变更的关联
PR 新增了 Druid 35.0.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中的下载 URL 直接指向 `dlcdn.apache.org`。该 URL 的选择是 PR 变更的一部分，因此失败由本次 PR 直接触发。该问题与模式01（Apache CDN Maven 版本 404）和模式38（ActiveMQ 下载源 404）根因相同——`dlcdn.apache.org` 不保证历史版本留存。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 `archive.apache.org/dist/`（Apache 归档站，保留所有历史版本），将 URL 改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

`archive.apache.org` 是 Apache 官方归档站点，长期保留所有已发布版本，不受 CDN 刷新策略影响。

### 方向 2（置信度: 中）
将下载源更换为华为云镜像站 `repo.huaweicloud.com/apache/druid/`，该镜像站在本仓库的其他 Dockerfile 中已验证可用（如模式01/模式33的历史修复中均使用过华为云镜像站）。

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 确实存在。如果 Apache Druid 35.0.0 在归档站也不可用（极端情况），则可能需要检查上游 Apache Druid 对该版本的实际发布状态。
- 如果 CI 环境存在 `archive.apache.org` 网络不可达的问题（参考模式33），则优先使用方向 2（华为云镜像站）。

## 修复验证要求
code-fixer 在提交修复前，必须使用 `curl -I` 或 `wget --spider` 验证新 URL 可正常访问（返回 HTTP 200），不应仅依赖假设。若新 URL 同样 404，需进一步调查 Apache Druid 35.0.0 是否已从所有 Apache 渠道撤回。
