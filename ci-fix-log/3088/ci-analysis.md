# CI 失败分析报告

## 基本信息
- PR: #3088 — chore(druid): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式01（Apache CDN Maven 版本 404）/ 模式38（ActiveMQ 下载源 404）
- 新模式标题: (已匹配现有模式)
- 新模式症状关键词: (已匹配现有模式)

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
- 失败位置: `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`:9（wget 下载命令）
- 失败原因: `dlcdn.apache.org` 是 Apache 的 CDN 分发节点，通常只保留最新版本，不保证历史版本的可用性。Druid 35.0.0 的二进制包已从该 CDN 下架（或从未上传至该节点），导致 `wget` 返回 HTTP 404。TCP 连接成功（DNS 解析和 TLS 握手均完成），排除网络不通问题。

### 与 PR 变更的关联
PR 新增了 `Bigdata/druid/35.0.0/24.03-lts-sp4/Dockerfile`，其中第 9 行的 `wget` 命令使用 `dlcdn.apache.org` 作为下载源。该 URL 在上游 CDN 中不存在（或已下架），是 PR 新增代码直接触发的失败。同一版本 35.0.0 的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）在较早提交时可能已成功构建过，说明该 CDN URL 在当时有效，但 CDN 现已移除该版本文件。

附：构建日志中还出现一个非致命 BuildKit 警告：
```
WARN: FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)
```
Dockerfile 第 3 行 `FROM ${BASE} as builder` 中 `as` 为小写而 `FROM` 为大写。此警告不导致构建失败，但建议统一为小写 `AS`。

## 修复方向

### 方向 1（置信度: 高）
将 Druid 35.0.0 的二进制包下载源从 `dlcdn.apache.org` 切换为 **Apache Archive**（`archive.apache.org`），该站点保留所有历史版本，不受 CDN 最新版策略影响。参考现有 Druid 32.0.1 SP1 Dockerfile 或其他使用 `archive.apache.org` 的 Dockerfile 的 URL 模式，确认 `archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否存在。

### 方向 2（置信度: 中）
如果 Apache Archive 中 Druid 35.0.0 也不可用，考虑将下载源切换到华为云 Apache 镜像站（如 `repo.huaweicloud.com/apache/druid/`）或其他已验证可用的 Apache 镜像。参考历史案例 PR #3077（Zookeeper 下载源从 archive 切换到 repo.huaweicloud.com）。

## 需要进一步确认的点
1. 确认 `https://archive.apache.org/dist/druid/35.0.0/apache-druid-35.0.0-bin.tar.gz` 是否存在且可访问。
2. 确认现有 SP2 的 `Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile` 是否也使用 `dlcdn.apache.org` 作为下载源——如果是，该 Dockerfile 在当前 CI 中也会构建失败（但可能不在本次 PR 的构建范围内）。
3. 如果 archive.apache.org 也不可用，需查询 Apache Druid 35.0.0 在各镜像站的可用性。

## 修复验证要求
- code-fixer 必须在修改 Dockerfile 中的下载 URL 前，先用 `curl -I` 或 `wget --spider` 验证新 URL 可返回 HTTP 200/301/302，避免替换后的 URL 同样 404。
- 如果改用 `archive.apache.org`，需确认该域名在 CI 构建环境中可达（历史模式 33 表明 `archive.apache.org` 在部分 CI 节点上可能存在网络不通的情况）。
- 同步检查同版本 35.0.0 的 SP2 Dockerfile（`Bigdata/druid/35.0.0/24.03-lts-sp2/Dockerfile`）的下载源是否需要一并修复，避免后续 PR 触发该 Dockerfile 构建时出现相同失败。
