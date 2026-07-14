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
#9 ERROR: process "/bin/sh -c wget https://dlcdn.apache.org/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile:9`（`RUN wget ...` 步骤）
- 失败原因: 下载 URL `https://dlcdn.apache.org/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 返回 HTTP 404，Apache CDN 不再托管该版本/路径的二进制包（与模式01 一致：`dlcdn.apache.org` 只保留当前最新版本，旧版本或该路径格式不可用后返回 404）

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中在 builder 阶段的第 9 行直接通过 `wget` 从 `dlcdn.apache.org` 下载 Druid 35.0.0 二进制包。该下载 URL 在 CI 构建时返回 404，是本次 PR 的 Dockerfile 内容直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 更换为 Apache 归档站 `archive.apache.org`（或其他已验证可达的镜像站如 `repo.huaweicloud.com`）。Apache 归档站长期保留所有历史版本，不受 CDN 只保留最新版的限制。对应 URL 应改为 `https://archive.apache.org/dist/druid/${VERSION}/apache-druid-${VERSION}-bin.tar.gz` 或等效镜像站地址。

### 方向 2（置信度: 中）
验证 Druid 35.0.0 在 Apache CDN 上的实际可用文件名与目录路径。当前 URL 路径格式 `/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 可能部分不正确（如目录名不是 `35.0.0` 而是 `druid-35.0.0`），导致即使 CDN 有文件也无法匹配。需确认上游 Apache Druid 在 CDN/归档站的真实路径结构后修正 URL。

## 需要进一步确认的点
- 现有 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 使用的下载源是什么（是否也是 `dlcdn.apache.org`，如果是则说明该源对 SP2 构建时可用但之后 CDN 移除了 35.0.0）
- Apache Druid 35.0.0 在 `archive.apache.org` 上的实际路径和文件名（`archive.apache.org/dist/druid/35.0.0/` 下是否存在 `apache-druid-35.0.0-bin.tar.gz`）

## 修复验证要求
code-fixer 在提交前，需通过 `wget --spider` 或 `curl -I` 验证修复后的下载 URL 确能返回 HTTP 200，而非仅凭推断写入 URL。可使用 `archive.apache.org/dist/druid/35.0.0/` 或 `repo.huaweicloud.com/apache/druid/35.0.0/` 先手动确认目标文件存在。
