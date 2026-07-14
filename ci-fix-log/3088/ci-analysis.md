# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式38
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
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
------
Dockerfile:9
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（wget 下载步骤）
- 失败原因: Dockerfile 中使用的下载源 `dlcdn.apache.org` 是 Apache CDN 分发节点，仅保留最新版本，不保证历史版本的可用性。Druid 35.0.0 的二进制包在该 CDN 上已不存在（或从未发布至此），导致 wget 返回 HTTP 404。

### 与 PR 变更的关联
PR #3088 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行 `wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 使用了 `dlcdn.apache.org` 作为下载源。该 URL 是造成 404 的直接原因，与 PR 变更直接相关。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org`（Apache CDN）更换为 `archive.apache.org`（Apache Archive），后者长期保留所有已发布版本。参考模式01 和模式38 的同类修复案例：
- URL 格式：`https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz`
- 或者更换为已验证可达的其他镜像站（如 `repo.huaweicloud.com`）。

## 需要进一步确认的点
- 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 文件确实存在（Apache Druid 35.0.0 是否已正式发布到 archive）。
- 如 archive 同样不可达，则需确认 Druid 35.0.0 是否已发布以及正确的官方下载路径。

## 修复验证要求
code-fixer 在提交修复前，必须手动验证新的下载 URL 确实可访问（使用 `wget --spider` 或 `curl -I` 检查 HTTP 200），确保修复后的 Dockerfile 可正常完成构建。
