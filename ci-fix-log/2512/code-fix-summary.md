# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构后缀，导致 x86_64 CI 构建时因架构不匹配而安装失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端安装方式从直接下载 RPM 并 `rpm -ivh` 安装，改为多阶段构建从官方 `foundationdb/foundationdb:${FDB_VERSION}` 镜像 `COPY` 二进制文件（`fdbcli` 和 `libfdb_c.so`），同时单独下载架构无关的 headers 包。

## 修复逻辑
CI 分析报告指出根因为 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 中 FoundationDB 客户端 RPM URL 硬编码为 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，在 x86_64 构建环境中无法安装。修复采用多阶段构建方式：
1. 新增构建阶段 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` — 官方镜像支持多架构（amd64/arm64），Docker 会自动拉取匹配目标架构的镜像。
2. 用 `COPY --from=fdb` 从官方镜像直接复制 `fdbcli` 和 `libfdb_c.so` 二进制文件，彻底消除 RPM 架构硬编码问题。
3. FoundationDB headers 包（`fdb-headers-7.3.77.tar.gz`）是架构无关的，通过独立 `RUN` 指令下载解压。

已从上游 `7.3.77` tag 获取 `packaging/docker/Dockerfile` 验证，FoundationDB 官方镜像将 `libfdb_c.so` 置于 `/usr/lib/libfdb_c.so`，当前 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` 路径映射正确。同时验证 GitHub Releases 中 `foundationdb-clients` RPM 确实存在 x86_64（el7）和 aarch64（el9）两架构版本，但 EL 版本不统一，故多阶段构建方案比动态 RPM URL 方案更稳健。

## 潜在风险
`COPY --from=fdb` 依赖 Docker Hub 上 `foundationdb/foundationdb:7.3.77` 镜像可用且支持目标架构。若该镜像未来被移除或架构支持变化，构建将失败。当前该镜像在多架构 manifest 中同时提供 amd64 和 arm64，风险较低。