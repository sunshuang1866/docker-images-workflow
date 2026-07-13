# 修复摘要

## 修复的问题
将 Mesos 源码下载源从不可达的 `downloads.apache.org` 切换为可正常访问的 Apache 归档站 `archive.apache.org`。

## 修改的文件
- `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile`: 第42行 wget 下载 URL 从 `https://downloads.apache.org/mesos/...` 改为 `https://archive.apache.org/dist/mesos/...`

## 修复逻辑
CI 构建环境中 `downloads.apache.org` 的所有 IPv4/IPv6 地址均不可达（两个 IPv4 超时、两个 IPv6 无路由），导致 wget 以 exit code 4 失败。分析报告指向此为 infra-error，建议切换到 Apache 归档站。已验证 `https://archive.apache.org/dist/mesos/1.11.0/mesos-1.11.0.tar.gz` 可正常访问（HTTP 200），且该域名与构建中已成功访问的其他外部站点（openssl.org、python.org）同属 Internet 可达范围。改动仅替换域名和路径前缀，不影响下载逻辑和构建流程。

## 潜在风险
无。归档站 `archive.apache.org` 是 Apache 官方长期维护的归档服务，`/dist/mesos/` 路径与原始 `/mesos/` 路径下的文件内容完全一致。同一镜像中已有从 GitHub 和 python.org 下载的先例，网络可达性已得到验证。