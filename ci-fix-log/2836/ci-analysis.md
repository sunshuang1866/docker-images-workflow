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
#9 134.4 curl: (28) Failed to connect to archive.apache.org port 443 after 134353 ms: Couldn't connect to server
#9 ERROR: process "/bin/sh -c curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz && ..." did not complete successfully: exit code: 28
------
Dockerfile:13
  13 | >>> RUN curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz && \
  14 | >>>     tar -zxvf /tmp/cassandra-${VERSION}.tar.gz -C /tmp && \
  15 | >>>     cd /tmp/apache-cassandra-${VERSION}/bin && \
  16 | >>>     rm -rf /tmp/cassandra-${VERSION}.tar.gz
------
Finished: FAILURE
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`
- 失败原因: CI 构建环境无法与 `archive.apache.org` 建立 TCP 443 端口连接，连接尝试持续约 134 秒后超时（exit code 28），导致 Cassandra 5.0.6 二进制包下载失败。

### 与 PR 变更的关联

PR 新增了 Cassandra 5.0.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。值得注意的是，**PR diff 中 Dockerfile 第 13 行的下载源为 `dlcdn.apache.org`**（`https://dlcdn.apache.org/cassandra/${VERSION}/...`），但 CI 实际执行时使用的 URL 为 `archive.apache.org`（`https://archive.apache.org/dist/cassandra/${VERSION}/...`）。这一 URL 差异暗示 CI 流水线中可能存在 URL 重写/转换机制，将 `dlcdn.apache.org` 替换为了 `archive.apache.org`；也可能是 CI 实际运行的 Dockerfile 版本与 PR diff 不一致。`archive.apache.org` 从当前 CI 构建环境不可达，导致 curl 连接超时。

此前的构建步骤（`yum install java`、`groupadd`/`useradd`）均已成功完成，说明基础镜像可用且包安装正常，问题仅限于 Cassandra 二进制包的下载阶段。

## 修复方向

### 方向 1（置信度: 高）

将 Dockerfile 中的下载源切换至 CI 构建环境网络可达的镜像站。历史同类案例（模式33：PR #3101、#3108、#3103）均通过将 `archive.apache.org` 替换为 `dlcdn.apache.org` 或 `repo.huaweicloud.com` 解决。若 CI 存在 URL 重写机制，需确认重写逻辑本身是否需要调整，而非仅修改 Dockerfile。

### 方向 2（置信度: 低）

若 CI 构建环境与 `archive.apache.org` 之间的网络不通是临时性的（如短暂防火墙规则变更），则重试构建即可。但基于历史模式33中多次出现同类问题，更可能是持续性的网络限制。

## 需要进一步确认的点

1. **CI 中实际运行的 Dockerfile 版本**：PR diff 中 URL 为 `dlcdn.apache.org`，但日志显示 `archive.apache.org`，需确认 CI 流水线是否对 URL 做了转换/替换，或是否有其他覆盖机制。
2. **从 CI 构建节点手动测试网络连通性**：在 CI 节点上执行 `curl -v --connect-timeout 10 https://archive.apache.org` 确认是否持续不可达。
3. **确认 Cassandra 5.0.6 在 `dlcdn.apache.org` 是否可用**：若 URL 重写机制将 `dlcdn.apache.org` → `archive.apache.org` 是全局行为，则需先修正确认重写逻辑。

## 修复验证要求

若修复方案为换源至 `repo.huaweicloud.com`，需确认目标 URL 在 CI 构建节点上能够正确响应 HTTP 200：
- 验证 URL：`https://repo.huaweicloud.com/apache/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz`
- 若使用 `dlcdn.apache.org`，需排除 CI URL 重写机制将该地址再次转为 `archive.apache.org` 的可能性。
