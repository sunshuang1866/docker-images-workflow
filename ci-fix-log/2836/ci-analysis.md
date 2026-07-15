# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式33
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 [4/5] RUN curl -o /tmp/cassandra-5.0.6.tar.gz https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz && ...
#9 134.4 curl: (28) Failed to connect to archive.apache.org port 443 after 134353 ms: Couldn't connect to server
#9 ERROR: process "/bin/sh -c curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz && ..." did not complete successfully: exit code: 28
------
Dockerfile:13
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`
- 失败原因: CI 构建环境无法与 `archive.apache.org` 的 443 端口建立 TCP 连接，curl 在超时 134 秒后退出（exit code 28），导致 Cassandra 5.0.6 二进制包下载失败。

### 关键发现：URL 与 PR diff 不一致

PR 的 Dockerfile diff 中下载 URL 明确写为：
```
https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz
```

但 CI 日志中实际执行的命令使用的是：
```
https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz
```

两个 URL 的域名和路径结构均不同（`dlcdn.apache.org/cassandra/` vs `archive.apache.org/dist/cassandra/`）。这说明 **CI pipeline 中存在 URL 重写机制**，将 `dlcdn.apache.org` 的 CDN 地址自动替换为 `archive.apache.org` 归档地址。`archive.apache.org` 当前在 CI 构建环境中不可达，导致下载失败。

### 与 PR 变更的关联

本次 PR 新增了 Cassandra 5.0.6 的 openEuler 24.03-LTS-SP4 Dockerfile，属于纯增量添加（新增文件 + README/meta 元数据更新）。失败与 PR 代码逻辑无关，是 CI 基础设施层（网络连通性）的问题。

## 修复方向

### 方向 1（置信度: 高）
将下载源切换为已验证可达的镜像站（如 `repo.huaweicloud.com`），避免对 `archive.apache.org` 的直接依赖。这与模式33的历史修复方法一致。

### 方向 2（置信度: 低）
使用 `dlcdn.apache.org` CDN 地址并阻止 CI pipeline 的 URL 重写——但这涉及 CI 基础设施配置变更，不在 Dockerfile 层面可控。如果 `dlcdn.apache.org` 对 Cassandra 5.0.6 的制品仍然有效（需验证），可绕过 URL 重写。

### 方向 3（置信度: 低）
等待 `archive.apache.org` 网络恢复后重试构建。此方向不涉及任何代码变更。

## 需要进一步确认的点

1. **URL 重写机制来源**：确认 CI pipeline 中哪个环节将 `dlcdn.apache.org` 替换为 `archive.apache.org`（例如 Jenkinsfile、构建脚本、proxy 配置），以及该替换的意图（是否是为了统一使用归档源以保证可重复构建）。
2. **`dlcdn.apache.org` 是否包含 Cassandra 5.0.6**：`dlcdn.apache.org` 是 Apache CDN 节点，通常只保留最新版本。需要验证 Cassandra 5.0.6 的二进制包是否仍在该 CDN 上可用。若已下架，直接使用 `dlcdn.apache.org` 也会失败，必须换用镜像站。
3. **华为云镜像站是否有 Cassandra 制品**：华为云镜像站（`repo.huaweicloud.com`）或其他国内镜像站是否托管了 Apache Cassandra 5.0.6 的二进制包，需在实施修复前确认。
4. **SP3 相同版本的验证**：已存在的 Cassandra 5.0.6 on SP3 是否也使用了同类 URL 且仍能通过 CI。如果 SP3 的 CI 最近也失败，说明是全局性网络问题而非本次 PR 独有。

## 修复验证要求

若采用方向 1（换镜像站），code-fixer 必须：
1. 确认目标镜像站（如 `repo.huaweicloud.com/apache/cassandra/`）中确实存在 Cassandra 5.0.6 的 `apache-cassandra-5.0.6-bin.tar.gz` 文件。
2. 验证新 URL 能够通过 `curl -I` 返回 HTTP 200 而非 404/302 到不可达地址。
3. 同时检查同版本 Cassandra 的其他已有 Dockerfile（如 SP3 版本）是否也需要同步更换下载源，以保持一致性。
