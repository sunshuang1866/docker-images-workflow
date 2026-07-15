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
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`（curl 下载步骤）
- 失败原因: CI 构建环境无法建立到 `archive.apache.org:443` 的 TCP 连接，curl 在尝试约 134 秒后超时（exit code 28）。与 PR 的 Dockerfile 本身无关，属于 CI 基础设施网络不可达问题。

### 与 PR 变更的关联
PR 新增的 Dockerfile 原始下载 URL 为 `https://dlcdn.apache.org/cassandra/${VERSION}/...`，但 CI 日志显示实际执行时 URL 已被转换为 `https://archive.apache.org/dist/cassandra/${VERSION}/...`（路径从 `/cassandra/` 变为 `/dist/cassandra/`，域名从 `dlcdn.apache.org` 变为 `archive.apache.org`）。CI 构建节点当前无法访问 `archive.apache.org`，导致下载超时。该网络问题不随 PR 变更内容而变，与 PR 代码无直接因果关联。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题——`archive.apache.org` 从当前构建节点不可达。需从 CI 运维层面排查：
- 构建节点的网络出口是否受防火墙/代理限制
- `archive.apache.org` 的 DNS 解析是否正常
- 是否需要调整 CI 流水线中的 URL 转换/镜像逻辑，改用其他可访问的镜像源（如 `dlcdn.apache.org` 或 `repo.huaweicloud.com`）

### 方向 2（置信度: 中）
如果 CI 层面的 URL 转换逻辑是为了绕过 CDN 可能出现的 404（参考历史模式01、模式38），则需确认 `dlcdn.apache.org/cassandra/5.0.6/` 路径当前是否可访问且返回 200。若 CDN 有该文件，建议 CI 直接使用 PR 中的原始 `dlcdn.apache.org` URL 而不做转换，可绕过 `archive.apache.org` 不可达的问题。

## 需要进一步确认的点
- `dlcdn.apache.org/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 是否当前可访问（200 OK）
- CI 流水线中将 `dlcdn.apache.org` 转换为 `archive.apache.org` 的具体转换规则及触发条件
- CI 构建节点能否通过其他方式（如 `wget` 或不同 DNS 配置）访问 `archive.apache.org`
