# CI 失败分析报告

## 基本信息
- PR: #3094 — chore(hbase): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式01
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#7 0.048 https://dlcdn.apache.org/hbase/2.6.5/hbase-2.6.5-bin.tar.gz
#7 0.282 curl: (22) The requested URL returned error: 404
#7 0.285 tar (child): hbase.tar.gz: Cannot open: No such file or directory
#7 0.285 tar (child): Error is not recoverable: exiting now
#7 ERROR: process "/bin/sh -c curl -fSL -o hbase.tar.gz https://dlcdn.apache.org/hbase/${VERSION}/hbase-${VERSION}-bin.tar.gz; ..." did not complete successfully: exit code: 2
------
Dockerfile:6
```

### 根因定位
- 失败位置: `Bigdata/hbase/2.6.5/24.03-lts-sp4/Dockerfile`:6
- 失败原因: `dlcdn.apache.org`（Apache CDN）不托管 HBase 2.6.5 的二进制包，curl 下载返回 HTTP 404，后续 tar 解压因文件不存在而失败。

### 与 PR 变更的关联
PR 新增了 `Bigdata/hbase/2.6.5/24.03-lts-sp4/Dockerfile`，其中的 `curl` 下载源使用了 `dlcdn.apache.org`。该 CDN 仅保留最新版本制品，HBase 2.6.5 在当前时间点已被 CDN 移除，导致下载 404。此失败直接由 PR 引入的 Dockerfile 造成。

## 修复方向

### 方向 1（置信度: 高）
将下载源从 `dlcdn.apache.org` 改为 `archive.apache.org/dist/hbase/`（Apache Archive），该归档站永久保留所有历史版本。URL 格式为：
`https://archive.apache.org/dist/hbase/${VERSION}/hbase-${VERSION}-bin.tar.gz`

### 方向 2（置信度: 中）
升级 `VERSION` 到当前 `dlcdn.apache.org` 上仍然可用的 HBase 最新版本。但考虑到已有 `2.6.5-oe2403sp3` 版本，这个方向可能造成版本不一致。

## 需要进一步确认的点
- 确认同仓库中已存在的 `Bigdata/hbase/2.6.5/24.03-lts-sp3/Dockerfile` 是否使用了相同的 `dlcdn.apache.org` 下载源，以及其构建是否仍然成功。如果 SP3 也未改用 archive 源，可能同样存在潜在风险。
- 确认 `archive.apache.org/dist/hbase/2.6.5/` 路径下确实包含 `hbase-2.6.5-bin.tar.gz` 文件。

## 修复验证要求
code-fixer 在提交前，需用 `curl -I` 或 `wget --spider` 验证目标下载 URL（archive.apache.org 路径）返回 HTTP 200，确认 HBase 2.6.5 二进制包在归档站确实可用。
