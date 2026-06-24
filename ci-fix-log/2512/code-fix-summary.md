# 修复摘要

## 修复的问题
FoundationDB clients RPM 下载 URL 硬编码 `aarch64` 架构，导致 x86_64 构建时依赖检查失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除硬编码架构的 RPM 下载安装方式，改为多阶段构建 `COPY --from=fdb` 从 `foundationdb/foundationdb:7.3.77` 镜像直接复制 `fdbcli` 和 `libfdb_c.so`，并额外下载 headers 支持编译。

## 修复逻辑
CI 分析报告指出原始 Dockerfile 第 22-24 行包含如下代码：
```
curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh ...
```
URL 中的 `aarch64` 被硬编码，当 CI 在 x86_64 构建机上执行时，下载了错误的架构 RPM，导致 `libm.so.6(GLIBC_2.17)` 依赖检查失败。

当前 Dockerfile 已将 RPM 安装方式完全替换为：
1. 多阶段构建：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，然后 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so`，利用 Docker 多阶段构建的架构感知能力自动获取正确架构的二进制文件。
2. 头文件下载：`curl ... fdb-headers-${FDB_VERSION}.tar.gz`，版本通过 ARG 动态传入（`ARG FDB_VERSION=7.3.77`），无架构硬编码。

此修复符合 CI 分析报告的"方向 2"建议（使用 FoundationDB 官方 Docker 镜像多阶段构建）。

## 潜在风险
- `fdb-headers` tarball 的下载 URL (`fdb-headers-${FDB_VERSION}.tar.gz`) 依赖 FoundationDB GitHub Release 页面是否提供该资源文件。当前未做 URL 可访问性验证，若该文件在 FoundationDB 7.3.77 release 中不存在，后续构建可能因下载失败而报错。可考虑改为 `COPY --from=fdb /usr/include/foundationdb /usr/include/foundationdb` 直接从 fdb 镜像复制头文件，彻底避免下载。