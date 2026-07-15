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
#9 [builder 3/3] RUN wget https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz     && tar -zxvf apache-druid-35.0.0-bin.tar.gz     && mv apache-druid-35.0.0 /opt/druid     && rm -f apache-druid-35.0.0-bin.tar.gz
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9-12`（`RUN wget ...` 步骤）
- 失败原因: `dlcdn.apache.org` CDN 不托管 Druid 35.0.0 的二进制 tarball — `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404。与知识库模式01（Apache CDN Maven 404）和模式38（ActiveMQ 下载源 404）同根：`dlcdn.apache.org` 是 Apache CDN 分发前端节点，通常只保留最新版本，历史版本下架后即返回 404。

### 与 PR 变更的关联
PR 的改动直接触发了此失败。新增的 Dockerfile 在构建阶段通过 `wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 下载 Druid 35.0.0，但该 URL 在 `dlcdn.apache.org` 上不存在。该问题与 Druid 35.0.0 版本本身无关（版本确实存在并发布过），仅因 CDN 不保留历史版本制品。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 下载源从 `dlcdn.apache.org` 换为 `archive.apache.org/dist/druid/`（Apache 官方归档站，保留所有历史版本），URL 格式如：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`

## 需要进一步确认的点
- 确认 `archive.apache.org/dist/druid/35.0.0/` 路径下确实存在 `apache-druid-35.0.0-bin.tar.gz`（通常归档站会保留已发布版本）
- 若 `archive.apache.org` 在 CI 环境不可达（参考模式33的历史案例），可考虑替换为华为云镜像站 `repo.huaweicloud.com/apache/druid/` 或其他可访问的镜像站

## 修复验证要求
code-fixer 必须验证目标下载 URL（`archive.apache.org` 或替代镜像站）在提交前确实可访问且返回 Druid 35.0.0 的完整 tarball，不能假定 URL 一定存在。可用 `wget --spider` 或 `curl -I` 验证新 URL 返回 200 而非 404。
