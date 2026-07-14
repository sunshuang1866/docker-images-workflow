# 修复摘要

## 修复的问题
将 Cassandra 5.0.6 二进制包的下载源从 CDN (`dlcdn.apache.org`) 切换为 Apache 官方归档站 (`archive.apache.org`)，解决 CDN 返回无效内容（196 字节 HTML 错误页）导致 tar 解压失败的问题。

## 修改的文件
- `Database/cassandra/5.0.6/24.03-lts-sp4/Dockerfile`: 第 13 行 curl 下载 URL 从 `dlcdn.apache.org/cassandra/` 改为 `archive.apache.org/dist/cassandra/`

## 修复逻辑
CI 构建日志显示 curl 从 `dlcdn.apache.org` 仅获取到 196 字节的非 gzip 内容（HTML 错误页），tar 解压失败。已从上游 `https://archive.apache.org/dist/cassandra/5.0.6/` 验证 `apache-cassandra-5.0.6-bin.tar.gz` (69MB) 确实存在且可正常访问。`archive.apache.org` 是 Apache 官方归档站，永久保留所有历史版本的 release 制品，不会出现 CDN 缓存未命中的问题。同一仓库中其他 77 处 Apache 制品下载均使用 `archive.apache.org`，本次修复保持与项目规范一致。

## 潜在风险
无。仅修改下载源域名，URL 路径结构和文件名完全一致，不会影响构建逻辑。