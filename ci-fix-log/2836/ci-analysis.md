# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式33
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
#9 134.3 curl: (28) Failed to connect to archive.apache.org port 443 after 134252 ms: Couldn't connect to server
#9 ERROR: process "/bin/sh -c curl -o /tmp/cassandra-${VERSION}.tar.gz https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz &&     tar -zxvf /tmp/cassandra-${VERSION}.tar.gz -C /tmp &&     cd /tmp/apache-cassandra-${VERSION}/bin &&     rm -rf /tmp/cassandra-${VERSION}.tar.gz" did not complete successfully: exit code: 28
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`（curl 下载步骤）
- 失败原因: CI 构建环境无法与 `archive.apache.org:443` 建立 TCP 连接，curl 在 134 秒后超时（exit code 28）

### 与 PR 变更的关联
PR 新增了 Cassandra 5.0.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile。该 Dockerfile 中的 curl 下载步骤触发了此失败。

**重要发现 — URL 不一致**：PR diff 中 Dockerfile 使用的下载 URL 为 `https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`，但 CI 实际执行时使用的是 `https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`。两者 host 和路径均不同（`dlcdn.apache.org/cassandra/` vs `archive.apache.org/dist/cassandra/`）。这暗示 CI 流程中存在 URL 改写/镜像层，将作者指定的 CDN 地址改写为了归档站地址，而归档站从当前 CI runner 网络不可达。

对比历史模式 33 的建议修复方向——"将下载源切换为已验证可达的 `dlcdn.apache.org`"——PR 作者原始使用的正是 `dlcdn.apache.org`，理论上应可行。失败的关键在于 CI 将其改写为 `archive.apache.org` 后网络不通。

## 修复方向

### 方向 1（置信度: 中）
**绕过 CI URL 改写**：将下载源从 Apache CDN/Archive 改为已验证可达的华为云镜像站（`repo.huaweicloud.com`）。参考历史模式 33 中已成功修复的同类案例（如 PR #3101、#3077），使用华为云镜像站可避免 Apache 服务器的网络可达性问题。

### 方向 2（置信度: 低）
**保留 `dlcdn.apache.org` 但排除 CI 改写**：如果 CI 的 URL 改写策略对某些 host 有例外规则（如 `dlcdn.apache.org` 或特定 URL pattern 不触发改写），可通过调整 URL 格式绕过改写，直接使用 `dlcdn.apache.org` 完成下载。需要确认 CI 网关/编排层的 URL 改写逻辑。

## 需要进一步确认的点
1. **CI URL 改写机制**：需确认 CI pipeline 中是否存在将 Apache 下载 URL 从 `dlcdn.apache.org` 自动改写为 `archive.apache.org` 的逻辑，以及该逻辑的触发条件和例外规则。
2. **`dlcdn.apache.org` 可达性**：从 CI runner 直接测试 `curl -I https://dlcdn.apache.org/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 是否可达，如果可达则问题仅在于 URL 改写层。
3. **华为云镜像站可用性**：确认 `https://repo.huaweicloud.com/apache/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 是否存在且可从 CI runner 访问。
4. **现有 sp3 Dockerfile 参考**：查看 `Database/cassandra/5.0.6/24.03-lts-sp3/Dockerfile` 使用的下载 URL，确认同一项目的其他 OS 版本是否也面临相同的网络问题。
