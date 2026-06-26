# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端安装步骤硬编码 `aarch64` 架构 RPM URL，在 x86_64 CI 构建环境上导致 RPM 依赖解析失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端安装方式从硬编码架构的 RPM 安装改为 Docker 多阶段构建 `COPY --from=fdb`，从官方 `foundationdb/foundationdb:7.3.77` 镜像中提取二进制文件。

## 修复逻辑
CI 分析报告指出根因为 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而 CI 构建环境实际运行在 x86_64 架构上。修复采用分析报告"方向 2"策略：

1. 在 Dockerfile 顶部新增 `ARG FDB_VERSION=7.3.77` 和 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建
2. 使用 `COPY --from=fdb` 从 FoundationDB 官方镜像提取 `fdbcli` 和 `libfdb_c.so`（二进制文件路径为 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so`）
3. 通过 GitHub Release 下载 `fdb-headers` tarball 获取头文件

此方案利用 Docker BuildKit 的平台自动匹配机制，构建时自动选择对应架构的 FoundationDB 镜像，从根本上消除了硬编码架构问题。

## 潜在风险
- FoundationDB 头文件通过 GitHub Release 下载，依赖网络可达性（已有 `--retry 5` 重试机制）
- `foundationdb/foundationdb:7.3.77` 镜像中的 `/usr/lib/libfdb_c.so` 被复制到 `/usr/lib64/libfdb_c.so`（目标路径为 64 位库目录），需确保基础镜像 `openeuler/openeuler:24.03-lts-sp3` 的库搜索路径包含该目录