# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构，导致 x86_64 CI 构建环境上 RPM 依赖解析失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 添加多阶段构建 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，通过 `COPY --from=fdb` 获取 `fdbcli` 和 `libfdb_c.so`，替代硬编码架构的 RPM 下载
  - 添加 FoundationDB 头文件单独下载（`fdb-headers-${FDB_VERSION}.tar.gz`），替代 RPM 安装时附带的头文件
  - 将 clang 库路径中的 `aarch64` 替换为动态 `ARCH=$(uname -m)`，支持多架构构建
  - 移除 `git clone --depth 1` 浅克隆，改为完整克隆，移除 `|| true` 静默错误掩盖
  - 移除运行时 yum install 中不存在的 `boost-foundation` 包
  - 移除构建期不必要的依赖包（`clang-tools-extra`, `rdma-core-devel`, `numactl-devel`, `python3-devel`, `autoconf`, `automake`, `libtool`）

## 修复逻辑
CI 分析报告的根因是 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 中 FoundationDB RPM URL 硬编码了 `aarch64`（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而 CI 构建环境为 x86_64。采用分析报告方向 2（多阶段构建方案）：从 FoundationDB 官方 Docker 镜像 `foundationdb/foundationdb:7.3.77` 中通过 `COPY --from=fdb` 直接获取编译好的客户端二进制（`/usr/bin/fdbcli`）和库文件（`/usr/lib/libfdb_c.so`），彻底避免 RPM 架构和依赖兼容性问题。同时将 clang 库路径中的硬编码 `aarch64` 改为 `$(uname -m)` 动态检测。

已从上游 `foundationdb/foundationdb` Dockerfile (tag 7.3.77) 验证：`/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径正确。已从 GitHub Releases 验证 `fdb-headers-7.3.77.tar.gz` 存在。

同时修复了分析报告指出的两个潜在后续问题：git 浅克隆无法 checkout commit hash（Pattern 18）和 `boost-foundation` 包不存在（Pattern 10）。

## 潜在风险
- 移除的构建期依赖包（`clang-tools-extra`, `rdma-core-devel`, `numactl-devel`, `python3-devel` 等）如果 3fs 源码编译实际需要，构建会失败。这些包在原始 PR 中存在但在修复中移除，需观察 CI 构建结果确认。
- FoundationDB 头文件 tarball 解压后的目录结构需确保与 3fs 源码 `#include` 路径匹配（期望 `/usr/include/foundationdb/fdb_c.h` 等）。