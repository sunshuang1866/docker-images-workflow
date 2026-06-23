# 修复摘要

## 修复的问题
Docker 构建时从 GitHub Releases 下载 Apache Kylin 5.0.3 二进制包返回 HTTP 404，将下载源切换至 Apache Archive。

## 修改的文件
- `Bigdata/kylin/5.0.3/24.03-lts-sp3/Dockerfile`: 将第 61 行 curl 下载 URL 从 `https://github.com/apache/kylin/releases/download/kylin-${VERSION}/apache-kylin-${VERSION}-bin.tar.gz` 改为 `https://archive.apache.org/dist/kylin/apache-kylin-${VERSION}/apache-kylin-${VERSION}-bin.tar.gz`

## 修复逻辑
CI 分析报告指出 GitHub Release URL `https://github.com/apache/kylin/releases/download/kylin-5.0.3/apache-kylin-5.0.3-bin.tar.gz` 返回 404。经验证：该 release tag 存在但制品不在 GitHub Releases 中。同时确认 `https://archive.apache.org/dist/kylin/apache-kylin-5.0.3/apache-kylin-5.0.3-bin.tar.gz` 返回 HTTP 200，且制品文件 `apache-kylin-5.0.3-bin.tar.gz` 存在于该目录中。修改后下载 URL 与同 Dockerfile 中 Hadoop、Hive、Zookeeper、Spark 等组件的下载方式保持一致（均使用 `archive.apache.org`）。

## 潜在风险
无。Apache Archive 是官方认可的发布渠道，制品文件名与 SHA256 校验文件均存在于目录中，下载方式与同 Dockerfile 内其他 Apache 组件一致。