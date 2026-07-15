# 修复摘要

## 修复的问题
将 Cassandra 5.0.6 下载源从 CI 不可达的 `archive.apache.org` 更换为与同版本其他变体一致的 `dlcdn.apache.org`。

## 修改的文件
- `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`: 第 13 行 curl 下载 URL 从 `https://archive.apache.org/dist/cassandra/` 改为 `https://dlcdn.apache.org/cassandra/`

## 修复逻辑
1. CI 日志显示 `archive.apache.org` 在构建环境中 TCP 连接超时（exit code: 28），与历史案例（模式33：accumulo、kyuubi、mesos）中的 Apache 镜像站网络不通问题一致。
2. 同仓库中其他 4 个 Cassandra Dockerfile（包括同版本 `5.0.6/24.03-lts-sp3`）均使用 `dlcdn.apache.org/cassandra/` 路径下载，且这些变体在 CI 中构建正常。
3. 当前 sp4 变体的 Dockerfile 使用了不一致的 `archive.apache.org/dist/cassandra/` URL，属于与其他变体不一致的代码问题。
4. 修复方案：将下载 URL 对齐为 `dlcdn.apache.org/cassandra/${VERSION}/apache-cassandra-${VERSION}-bin.tar.gz`，与 `5.0.6/24.03-lts-sp3` 完全一致。

## 潜在风险
无。`dlcdn.apache.org` 已被同仓库的 `5.0.6/24.03-lts-sp3` 变体验证可用，且 CDN 同时托管 5.0.6 版本的制品。