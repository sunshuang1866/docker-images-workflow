# 修复摘要

## 修复的问题
修复 Kyuubi Dockerfile 中两个问题：(1) Apache 下载源在 CI aarch64 runner 上网络不可达；(2) BUILDARCH 变量与 BuildKit 预定义全局 ARG 冲突导致 JDK 下载 URL 架构字符串错误。

## 修改的文件
- `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`:
  - 第 17 行：将 Kyuubi 下载源从 `downloads.apache.org` 切换为 `dlcdn.apache.org`
  - 第 28-34 行：将 JDK 下载 RUN 命令中的 `BUILDARCH` 变量重命名为 `JAVA_ARCH`，避免与 BuildKit 预定义全局 ARG 冲突

## 修复逻辑

**修复 1 — 下载源切换**：CI aarch64 runner（`ecs-build-docker-aarch64-01-sp`）无法与 `downloads.apache.org` 建立 TCP 连接（所有 IPv4/IPv6 地址均超时或不可达），导致 `wget` 退出码 4。已将下载源切换为 `dlcdn.apache.org`，这是本仓库中 58 个其他 Dockerfile（Hadoop、Flink、Druid、HBase、Hive 等）统一使用的 Apache CDN 域名。已从上游确认 `https://dlcdn.apache.org/kyuubi/kyuubi-1.11.1/apache-kyuubi-1.11.1-bin.tgz`（224M）存在。

**修复 2 — BUILDARCH 变量冲突**：`BUILDARCH` 是 BuildKit 预定义全局 ARG（值为构建宿主机架构），在 RUN 中对其重新赋值的 shell 变量无法生效，导致 JDK 下载 URL 中的架构字符串使用 BuildKit 原始值（如 `amd64`）而非期望值（`x64`），产生 404。已将变量重命名为 `JAVA_ARCH`，避免与 BuildKit 预定义变量冲突。

## 潜在风险
- `dlcdn.apache.org` 在 CI 环境中应可正常访问（本仓库大量同类镜像已使用该 CDN），但若 CDN 节点不可用，可回退至 `archive.apache.org`。
- `JAVA_ARCH` 重命名不影响其他功能，`ARG BUILDARCH` 声明保留但不再被引用，无副作用。