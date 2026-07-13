# 修复摘要

## 修复的问题
CI 构建环境无法连接 `archive.apache.org` 下载 Mesos 1.11.0 源码包，导致 Docker 构建在 wget 阶段超时失败。

## 修改的文件
- `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile`: 将 Mesos 源码下载 URL 从 `https://archive.apache.org/dist/mesos/` 替换为 `https://repo.huaweicloud.com/apache/mesos/`

## 修复逻辑
CI 构建节点的网络无法访问 `archive.apache.org`（TCP 连接超时），该类 Apache 镜像站在当前 CI 环境中不可达。已从上游验证 `https://repo.huaweicloud.com/apache/mesos/1.11.0/mesos-1.11.0.tar.gz` 返回 HTTP 200（Content-Length: 72210031），文件存在且可下载。华为云镜像站在同类 CI 失败（PR #3077 accumulo）中已验证可达，修复方向与历史案例一致。

## 潜在风险
无。仅替换下载源 URL，镜像站路径结构与 Apache 官方一致（`/apache/mesos/${VERSION}/`），不改变文件内容、构建逻辑或其他步骤。