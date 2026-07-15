# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式33
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

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
- 失败原因: CI 构建环境（aarch64 runner）无法通过 TCP 连接 `archive.apache.org:443`，curl 在 ~134 秒后超时（exit code: 28）。属于 CI 基础设施网络不可达问题，与 PR 代码变更无关。

### 值得注意的 URL 差异
PR diff 中 Dockerfile 第 13 行指定的下载 URL 为 `https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`，但 CI 实际执行时却使用了 `https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz`。二者在域名（`dlcdn.apache.org` vs `archive.apache.org`）和路径前缀（`cassandra/` vs `dist/cassandra/`）上均不同。说明 CI 编排层可能有 URL 重写或代理转换机制，导致实际请求走到了不可达的 `archive.apache.org`。

### 与 PR 变更的关联
**无关**。PR 变更仅新增了 Cassandra 5.0.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 构建前两个步骤（`yum install java`、`groupadd/useradd`）均已成功完成（#7 DONE, #8 DONE），直到 curl 下载 Apache 制品时因网络不可达而失败。该网络问题与 PR 代码无关，任何需要从 `archive.apache.org` 下载制品的 PR 在该 CI 环境下都会同样失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施网络问题（`archive.apache.org` 从当前 aarch64 runner 不可达），与 Dockerfile 内容无关。建议：
- 重新触发 CI 构建，确认是否为临时网络波动。
- 若 `archive.apache.org` 持续不可达，CI 运维团队需排查 runner 节点的网络/防火墙/DNS 配置，或调整 CI 的 URL 重写规则，使下载请求走可达的镜像源（如 `dlcdn.apache.org`、`repo.huaweicloud.com` 等）。
- 参考历史模式 33（Apache 镜像站网络不通）中的类似处理方式。

## 需要进一步确认的点
1. CI 编排层是否有 URL 重写/代理转换规则，将 `dlcdn.apache.org` 请求改写为 `archive.apache.org`？若有，该规则是否存在配置错误（例如路径前缀转换不正确）？
2. `archive.apache.org` 在 CI runner 节点上的网络可达性——是临时超时还是永久不可达？从当前 aarch64 runner 上执行 `curl -v https://archive.apache.org` 测试网络连通性。
3. `dlcdn.apache.org` 在 CI runner 节点上是否可达？若可达，是否可以绕开 URL 重写直接使用？
