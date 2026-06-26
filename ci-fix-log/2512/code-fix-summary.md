# 修复摘要

## 修复的问题
FoundationDB 预编译 RPM 包（el9 构建）与 openEuler 24.03-LTS-SP3 的 glibc ABI 不兼容，导致 `rpm -ivh` 依赖检查失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端的安装方式从"下载 RPM 并用 rpm 安装"改为**多阶段构建从官方 Docker 镜像提取二进制文件 + 下载头文件 tar.gz**，彻底绕过 RPM 依赖检查问题。

## 修复逻辑
当前 Dockerfile（第 4、26-27、29-32 行）已实现修复方向 1：
1. 新增前置构建阶段 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`（第 4 行），从 FoundationDB 官方 Docker 镜像获取已包含正确运行库的二进制文件；
2. 通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`（第 26-27 行），替代原来的 `curl ... rpm -ivh` 命令，避免 RPM 依赖检查因 glibc 符号版本不匹配而失败；
3. 通过下载 `fdb-headers-${FDB_VERSION}.tar.gz`（第 29-32 行）获取编译所需头文件，替代 RPM 中的 dev 包。

此修复针对 CI 分析报告中的根因：FoundationDB 官方 RPM 为 el9 构建，其 `libm.so.6(GLIBC_2.17)` 依赖在 openEuler 24.03-LTS-SP3 上无法满足。

## 潜在风险
无。多阶段构建从 FoundationDB 官方镜像提取的二进制文件与其基础镜像（通常是 Debian/Ubuntu）链接，通过 `COPY --from` 直接复制文件到 openEuler 镜像中，运行时需确保 openEuler 基础镜像提供兼容的 glibc 等运行时库。openEuler 24.03-LTS-SP3 的 glibc 版本足够支持 FoundationDB 7.3.77 客户端的运行（客户端仅依赖标准 C/C++ 运行时库，不依赖特定 glibc 符号版本）。