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
#9 0.057 --2026-07-10 04:55:51--  https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz
#9 0.087 Resolving dlcdn.apache.org (dlcdn.apache.org)... 151.101.2.132, 2a04:4e42::644
#9 0.459 Connecting to dlcdn.apache.org (dlcdn.apache.org)|151.101.2.132|:443... connected.
#9 0.470 HTTP request sent, awaiting response... 404 Not Found
#9 0.655 2026-07-10 04:55:51 ERROR 404: Not Found.
------
Dockerfile:9
ERROR: failed to solve: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`
- 失败原因: `dlcdn.apache.org` 只托管当前最新版本，Apache Druid 35.0.0 已从 CDN 下架（返回 404）。现有 SP2 Dockerfile 使用了相同的 URL 格式且当时构建成功（说明 35.0.0 曾经可用），但此后 Apache CDN 因新版本发布移除了旧版本制品。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其下载 URL 为 `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz`。URL 格式本身正确（与已有的 24.03-lts-sp2 Dockerfile 完全一致），但上游 Apache CDN 已不再托管 35.0.0 版本，导致 wget 返回 404、构建失败。与 PR 代码逻辑错误无关，属于上游制品可用性变更。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（仅保留最新版本）切换至 `archive.apache.org`（保留历史版本），即 URL 从 `https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实可用（在 CI 网络环境下 `wget` 可达）。
- 若 `archive.apache.org` 在 CI 环境中也不可达（参考模式33），可改用华为云镜像站 `repo.huaweicloud.com` 对应的 Apache 镜像路径。

## 修复验证要求
code-fixer 在提交前，需手动执行 `wget --spider https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 验证目标 URL 确实可访问且返回 200 OK，确认后再提交修改。
