# 修复摘要

## 修复的问题
CI 构建环境中 `downloads.apache.org` 网络不可达，导致 wget 下载 Knox 2.1.0 超时失败（exit code: 4），将下载源切换为已验证可达的 `dlcdn.apache.org`。

## 修改的文件
- `Bigdata/knox/2.1.0/24.03-lts-sp4/Dockerfile`: 第 21 行 Knox 下载 URL 从 `downloads.apache.org` 改为 `dlcdn.apache.org`

## 修复逻辑
同一 Dockerfile 中第 12 行的 Hadoop 从 `dlcdn.apache.org` 下载成功（耗时 ~39s），证明 CI 环境可正常访问该 CDN。分析报告也指出 `downloads.apache.org` 所有 IPv4/IPv6 地址均连接超时，属于 CI 网络层面的问题。已通过 WebFetch 验证 `https://dlcdn.apache.org/knox/2.1.0/knox-2.1.0.zip` 可正常访问（返回 200），Knox 制品确实托管在 CDN 上。此修复是最小化改动，仅替换域名，与同文件中 Hadoop 的下载源保持一致。

## 潜在风险
无。`dlcdn.apache.org` 是同一次构建中已验证可用的 Apache CDN 地址，Knox 2.1.0 制品在该 CDN 上确认存在且可访问。