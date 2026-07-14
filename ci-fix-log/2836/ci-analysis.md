# CI 失败分析报告

## 基本信息
- PR: #2836 — chore(cassandra): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式（相近模式：模式01 / 模式32）
- 新模式标题: CDN下载内容无效
- 新模式症状关键词: gzip: stdin: not in gzip format, dlcdn.apache.org, 196 bytes, curl, tar

## 根因分析

### 直接错误
```
#9 [4/5] RUN curl -o /tmp/cassandra-5.0.6.tar.gz \
    https://dlcdn.apache.org/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz && \
    tar -zxvf /tmp/cassandra-5.0.6.tar.gz -C /tmp && \
    cd /tmp/apache-cassandra-5.0.6/bin && \
    rm -rf /tmp/cassandra-5.0.6.tar.gz
#9 0.066 
100   196  100   196    0     0    846      0 --:--:-- --:--:-- --:--:--   848
#9 0.300 
#9 0.300 gzip: stdin: not in gzip format
#9 0.300 tar: Child returned status 1
#9 0.300 tar: Error is not recoverable: exiting now
#9 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 2
------
Dockerfile:13
```

### 根因定位
- 失败位置: `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`:13（`RUN curl ... && tar ...` 步骤）
- 失败原因: curl 从 `dlcdn.apache.org` 下载 Cassandra 5.0.6 二进制包仅获取到 196 字节的非 gzip 内容（极可能为 HTML 错误页），tar 解压时因格式不符而退出（exit code: 2）。curl 本身未报告 HTTP 错误状态码，说明 CDN 以 200 状态返回了错误页面/重定向页面而非实际二进制文件。

### 与 PR 变更的关联
**直接关联**。PR 新增的 `Dockerfile`（第13-16行 RUN 指令）使用 `https://dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz` 作为下载源。该 CDN URL 未能提供有效的 Cassandra 二进制包，导致 Docker 构建失败。这是本次 PR 引入的新 Dockerfile 暴露出的下载源不可用问题，而非由于代码逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 切换为 Apache 官方归档站 `archive.apache.org`：
`https://archive.apache.org/dist/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`
- `archive.apache.org` 永久保留所有历史版本的 release 制品，不依赖 CDN 边缘节点缓存
- 历史模式33（Apache 镜像站网络不通）表明 `archive.apache.org` 在 CI 环境中已验证可达（或可进一步通过华为云镜像站 `repo.huaweicloud.com/apache/cassandra/` 替代）

### 方向 2（置信度: 中）
若 `archive.apache.org` 同样不可达，可尝试华为云镜像站：
`https://repo.huaweicloud.com/apache/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`
历史模式01/33 中华为云镜像站多次作为备选下载源成功使用。

## 需要进一步确认的点
1. **验证 URL 可用性**：确认 `https://archive.apache.org/dist/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 是否确实存在且可下载完整二进制包（预期大小约 40-60MB，远大于 196 字节）。
2. **现有 SP3 Dockerfile 对比**：确认 `Database/cassandra/5.0.6/24.03-lts-sp3/Dockerfile` 使用的下载源是否为同一 CDN URL。若 SP3 也使用 `dlcdn.apache.org` 且当前 CI 仍能通过，则本次失败可能是 CDN 临时性问题，重试即可恢复；若 SP3 使用其他源，则按方向1修复。
3. **文件名差异排除**：确认上游 Cassandra 5.0.6 二进制文件名确实为 `apache-cassandra-5.0.6-bin.tar.gz`（而非 `apache-cassandra-5.0.6-bin.tar.gz.sha256` 等变体），可在浏览器中验证 `https://archive.apache.org/dist/cassandra/5.0.6/` 目录下的实际文件列表。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本修复为 URL 替换，不涉及正则 patch。
