# 修复摘要

## 修复的问题
Apache CDN (`dlcdn.apache.org`) 上 Hive 4.1.0 二进制包已不存在（返回 404），Docker 构建下载失败。

## 修改的文件
- `Bigdata/hive/4.1.0/24.03-lts-sp4/Dockerfile`: 将 Hive 下载源从 `dlcdn.apache.org` 切换为 `archive.apache.org/dist/hive/`

## 修复逻辑
根因是 `dlcdn.apache.org/hive/hive-4.1.0/` 已移除 Hive 4.1.0 的二进制包，导致 curl 返回 404。Apache 归档站 (`archive.apache.org/dist/`) 保留所有历史版本，不会移除。已从上游 `archive.apache.org/dist/hive/hive-4.1.0/apache-hive-4.1.0-bin.tar.gz` 验证，文件可正常访问（返回大文件内容，确认为有效 tar.gz）。

改动仅将第 7 行的域名从 `dlcdn.apache.org` 改为 `archive.apache.org/dist`：
```
- https://dlcdn.apache.org/hive/hive-4.1.0/apache-hive-4.1.0-bin.tar.gz
+ https://archive.apache.org/dist/hive/hive-4.1.0/apache-hive-4.1.0-bin.tar.gz
```

## 潜在风险
无。此为最小化改动，仅切换 Hive 下载源域名，不影响其他逻辑。Hadoop 下载仍使用 `dlcdn.apache.org`，但因 Hadoop 3.4.1 当前仍在 CDN 上托管，未受影响。