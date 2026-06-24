# 修复摘要

## 修复的问题
FoundationDB RPM 下载 URL 中硬编码了 `aarch64` 架构标识，导致在 x86_64 CI 构建 job 上 `rpm -ivh` 因架构不匹配而失败（`libm.so.6(GLIBC_2.17)` 依赖无法满足）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端库的安装方式从直接下载 RPM 改为 Docker 多阶段构建，从 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY` 所需文件；同时修复了浅克隆导致的 checkout 失败风险和 clang 库路径架构自适应问题。

## 修复逻辑
CI 分析报告的根因是 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64`，未进行架构自适应。修复采用多阶段构建方案：

1. 添加 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 作为构建阶段
2. 通过 `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` 获取 FoundationDB 客户端
3. 通过 `curl` 单独下载 `fdb-headers-${FDB_VERSION}.tar.gz` 提供编译所需头文件

已验证 `foundationdb/foundationdb:7.3.77` 在 Docker Hub 上为多架构镜像（amd64 + arm64），Docker 会自动拉取匹配构建架构的镜像，彻底消除了架构硬编码问题。

同步修复了两项关联问题：
- 移除 `git clone --depth 1`，避免浅克隆导致 `git checkout ${VERSION}` 无法访问指定 commit hash
- 在 cmake 构建前添加 `ARCH=$(uname -m)`，实现 clang 编译器运行时库路径的架构自适应

## 潜在风险
- `foundationdb/foundationdb:7.3.77` 镜像基于 Rocky Linux 9.4（glibc 2.34），与 openEuler 24.03-lts-sp3 的 glibc 版本可能存在差异。但 glibc 具有向后兼容性，且 FoundationDB 官方以此方式分发客户端库，风险较低。
- 修复依赖 `foundationdb/foundationdb:7.3.77` 镜像持续可用，若该镜像未来被废弃需更新为其他获取方式。