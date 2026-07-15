# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.051   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
#9 0.051                                  Dload  Upload   Total   Spent    Left  Speed
#9 0.051
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100   196  100   196    0     0  11035      0 --:--:-- --:--:-- --:--:-- 11529
#9 0.071
#9 0.071 gzip: stdin: not in gzip format
#9 0.071 tar: Child returned status 1
#9 0.071 tar: Error is not recoverable: exiting now
#9 ERROR: process "/bin/sh -c curl -o /tmp/cassandra-${VERSION}.tar.gz https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz &&     tar -zxvf /tmp/cassandra-${VERSION}.tar.gz -C /tmp &&     cd /tmp/apache-cassandra-${VERSION}/bin &&     rm -rf /tmp/cassandra-${VERSION}.tar.gz" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile:13`（`RUN curl ... tar -zxvf ...` 步骤）
- 失败原因: `dlcdn.apache.org` 对 Cassandra 5.0.6 的二进制包只返回了 **196 字节**的响应（极可能是 HTML 404/错误页面），`curl` 下载完成但 `tar -zxvf` 解压时发现内容不是 gzip 格式，导致构建失败。

### 与 PR 变更的关联
PR 变更直接触发了该失败。PR 新增了 `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`，其中第 13 行使用 `dlcdn.apache.org` 作为 Cassandra 二进制包的下载源。该 CDN 遵循 Apache 的惯例——仅保留各项目的最新版本，历史版本（如 Cassandra 5.0.6）可能已被下架，与知识库中**模式01**（Apache CDN Maven 404）和**模式38**（ActiveMQ 下载源 404）的根因完全一致。PR 本身的 Dockerfile 写法、版本号、元数据均无错误。

## 修复方向

### 方向 1（置信度: 高）
将 Cassandra 5.0.6 的下载源从 `dlcdn.apache.org` 替换为 `archive.apache.org`（Apache 官方归档站，永久保留历史版本），或替换为已验证可达的国内镜像站（如 `repo.huaweicloud.com`）。URL 格式需对应调整为归档路径：`https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`。

### 方向 2（置信度: 中）
若 `archive.apache.org` 也不可达（参照模式33中部分 Apache 域名在 CI 环境网络不通的情况），可改用华为云镜像站或其他已证实 CI 环境可达的镜像源。

## 需要进一步确认的点
1. 确认 Cassandra 5.0.6 在 `archive.apache.org`（`https://archive.apache.org/dist/cassandra/5.0.6/`）上确实存在该二进制包。
2. 检查同仓库下已有的 `Database/cassandra/5.0.6/24.03-lts-sp3/Dockerfile` 是否使用相同的 `dlcdn.apache.org` 下载源——如果 SP3 版本仍在正常构建，则可能是 CDN 的间歇性问题；如果 SP3 也失败，则确认是版本下架问题。

## 修复验证要求
code-fixer 必须在提交前手动验证新的下载 URL 可访问且返回的是有效的 gzip 压缩包（而非 HTML 页面）。可用 `curl -sI <新URL>` 确认 HTTP 状态码为 200，且 `Content-Type` 为 `application/x-gzip` 或类似二进制类型的响应。
