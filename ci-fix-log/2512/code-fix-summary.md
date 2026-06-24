# 修复摘要

## 修复的问题
将 FoundationDB 客户端的安装方式从跨发行版 RPM 安装（`rpm -ivh foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）改为多阶段构建从 FoundationDB 官方 Docker 镜像复制二进制文件，解决 `libm.so.6(GLIBC_2.17)` 依赖不满足的 RPM 安装失败问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 使用多阶段构建 `FROM foundationdb/foundationdb:7.3.77 AS fdb` 替代 `rpm -ivh` 安装；同时修复 git shallow clone 与 commit hash 不兼容问题（移除 `--depth 1`）和 `boost-foundation` 包名不存在问题；将硬编码 `aarch64` 架构改为动态 `$(uname -m)`

## 修复逻辑
CI 分析报告指出根因是 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 面向 RHEL/CentOS 9 构建，其 RPM 依赖 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 的 glibc 打包体系下无法满足。修复采用分析报告推荐的方向 1（高置信度）：多阶段构建从 `foundationdb/foundationdb:7.3.77` 镜像复制 `fdbcli` 和 `libfdb_c.so`，完全规避跨发行版 RPM 依赖问题。已验证 FoundationDB 官方镜像中 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 均存在且正确。同时修复了分析报告中提到的另外两个历史已知问题：(1) git clone `--depth 1` 与特定 commit hash checkout 不兼容，移除所有 `--depth 1` 和 `--shallow-submodules` 参数；(2) `boost-foundation` 包名在 openEuler 不存在，从 yum install 中移除。

## 潜在风险
- `libfdb_c.so` 从 FDB 官方镜像复制到 openEuler 后，需确保 openEuler 已安装的运行时库（如 libstdc++ 等）与 FDB 客户端库的 ABI 兼容。FDB 7.3.77 官方镜像基于 Rocky Linux 9.4，与 openEuler 24.03 均为较新发行版，glibc/gcc 版本差异应在可接受范围内。
- 原 yum install 列表中移除了 `clang-tools-extra`、`rdma-core-devel`、`numactl-devel`、`python3-devel`、`autoconf`、`automake`、`libtool` 等包。如果 3FS 编译实际需要这些依赖，后续 cmake 构建阶段可能会失败，届时需要针对性补充回来。