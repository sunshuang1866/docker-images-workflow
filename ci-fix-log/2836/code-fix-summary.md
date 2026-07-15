# 修复摘要

## 修复的问题
Dockerfile 中 curl 下载 Cassandra 5.0.6 二进制包时，`archive.apache.org` 在 CI runner 环境中网络不可达导致连接超时（exit code 28）。

## 修改的文件
- `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`: 将 curl 下载 URL 从 `https://archive.apache.org/dist/cassandra/...` 改为 `https://repo.huaweicloud.com/apache/cassandra/...`

## 修复逻辑
1. 根因：CI build 环境中无法与 `archive.apache.org:443` 建立 TCP 连接，curl 在 134 秒后超时。
2. 已从上游验证 `https://repo.huaweicloud.com/apache/cassandra/5.0.6/apache-cassandra-5.0.6-bin.tar.gz` 返回 HTTP 200，Content-Length: 72645918，文件完整可用。
3. 同时验证 `https://dlcdn.apache.org/cassandra/5.0.6/` 返回 404（该路径在 CDN 上不存在），因此不能直接沿用其他 Dockerfile 中使用的 `dlcdn.apache.org` URL。
4. 使用华为云镜像站 `repo.huaweicloud.com` 绕过 CI URL 改写机制和 Apache 官方服务器网络不可达问题，与历史案例 PR #3101、#3077 修复方式一致。

## 潜在风险
华为云镜像站是 openEuler 生态常用镜像源，可用性高。无其他风险。