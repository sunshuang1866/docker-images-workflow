# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [4/5] RUN curl -o /tmp/cassandra-5.0.6.tar.gz https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz && ...
#9 0.097   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#9 0.097                                  Dload  Upload   Total   Spent    Left  Speed
#9 134.4 curl: (28) Failed to connect to archive.apache.org port 443 after 134353 ms: Couldn't connect to server
#9 ERROR: process "/bin/sh -c curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz && ..." did not complete successfully: exit code: 28
------
Dockerfile:13
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`（curl 下载步骤）
- 失败原因: CI 构建环境中 `archive.apache.org` 网络不可达，curl 在 134 秒后 TCP 连接超时（exit code: 28），导致 Docker 镜像构建失败。这与模式33（Apache 镜像站网络不通）高度吻合——历史案例（PR #3108 mesos、PR #3103 kyuubi、PR #3077 accumulo）中 `archive.apache.org` 在 CI 环境中多次出现同样的不可达问题。

### 与 PR 变更的关联

**存在 URL 不一致问题需要关注**：PR diff 中新增的 Dockerfile 下载 URL 使用的是 `dlcdn.apache.org`（Apache CDN），但 CI 日志中实际构建时访问的是 `archive.apache.org`（Apache 归档站）。两者不一致，可能原因：

1. CI 流水线在某处对 URL 做了重写/替换（如构建脚本中统一替换 CDN URL 为归档站 URL）
2. 或者日志来自不同于 PR diff 所对应的构建步骤

无论哪种情况，实际构建失败的根因与 PR 代码本身无关——这是 CI 基础设施网络连通性问题，即使 Dockerfile 使用 `dlcdn.apache.org` 也可能因为 `archive.apache.org` 的替换而失败。

## 修复方向

### 方向 1（置信度: 高）
**将下载源从 `archive.apache.org`（或被 CI 替换后的目标 URL）更换为已验证可达的镜像源**，如 `repo.huaweicloud.com`（华为云镜像站）或切换为 Dockerfile diff 中原本指定的 `dlcdn.apache.org`（确认 CI 不干预 URL 替换的前提下）。历史案例（模式33）中，accumulo（PR #3077）通过切换到 `repo.huaweicloud.com` 解决了同样的问题。具体需要确认 Cassandra 5.0.6 的二进制包在目标镜像站上是否存在。

### 方向 2（置信度: 中）
**排查 CI 流水线是否存在 URL 重写逻辑**。PR diff 中 Dockerfile 使用的 URL 是 `dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`，而 CI 日志显示实际访问的是 `archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`。如果 CI 在 Docker 构建前对 Dockerfile 做了 URL 替换，应直接在 CI 层面修复替换逻辑，使其指向可用镜像站。

## 需要进一步确认的点
1. CI 流水线中是否有对 Dockerfile 下载 URL 做集中的 `archive.apache.org` 替换逻辑？如果有，需要确认替换规则并改为指向可用镜像站
2. Cassandra 5.0.6 制品在 `dlcdn.apache.org` 上是否当前可用？（CDN 通常只保留最新版本，5.0.6 可能已下架，参考模式01）
3. 确认目标替换镜像站（如 `repo.huaweicloud.com`）上是否有 `apache-cassandra-5.0.6-bin.tar.gz` 可用
