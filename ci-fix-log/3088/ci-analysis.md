# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01 / 模式38
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

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
- 失败原因: Dockerfile 中 `wget` 从 `dlcdn.apache.org` 下载 Apache Druid 35.0.0 二进制包时返回 HTTP 404。`dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，历史版本（如 Druid 35.0.0，发布于 2025 年底）下架后返回 404。此根因与模式01（Maven CDN 404）、模式38（ActiveMQ CDN 404）完全一致。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile` 文件（全新文件，35 行），其中第 9 行硬编码了从 `dlcdn.apache.org` 下载的 wget 命令。该 URL 在 CI 构建时已不可达，直接导致构建失败。失败由本次 PR 的代码变更直接触发。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org`，归档站保留所有历史版本，不会因版本过旧而 404。具体将 URL：
`https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
改为：
`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
（需确认 `archive.apache.org/dist/druid/` 路径下确实存在该文件的准确路径结构。）

### 方向 2（置信度: 中）
如果 `archive.apache.org` 同样不可达（参考模式33，历史上有多个案例 `archive.apache.org` 在 CI 环境中网络不通），可换用华为云镜像站 `https://repo.huaweicloud.com/apache/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`，该镜像站在本站其他 PR 中已验证可用（如 PR #3077、#3103、#3108）。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否确实存在（即 Apache Druid 在归档站的路径结构是否为 `/dist/druid/{version}/apache-druid-{version}-bin.tar.gz`）。
- 确认 CI 构建环境是否能访问 `archive.apache.org`（历史上有多个案例 `archive.apache.org` 在 CI 环境中不可达，需考虑备用镜像站）。

## 修复验证要求
code-fixer 在提交前，需从浏览器或 `curl -I` 验证新的下载 URL 是否返回 HTTP 200（而非 404），确认目标文件确实存在于所选的下载源中。建议同时测试 `archive.apache.org` 和 `repo.huaweicloud.com` 两个候选源，选择在 CI 环境中可达且文件确实存在的源。
