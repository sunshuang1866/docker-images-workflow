# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端库的安装方式从硬编码架构 RPM 下载改为多阶段构建 COPY，消除了 aarch64 RPM 在 x86_64 构建节点上的依赖失败问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除硬编码架构的 `foundationdb-clients` RPM 下载安装步骤（原 `rpm -ivh` / `rpm2cpio | cpio`），改为多阶段构建 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb` 从官方多架构镜像获取 `fdbcli` 和 `libfdb_c.so`。

## 修复逻辑
CI 分析报告指出原 Dockerfile 第 22 行硬编码了 `aarch64` 架构的 FoundationDB RPM URL（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），在 x86_64 CI 构建节点上执行时因架构不匹配导致 `libm.so.6(GLIBC_2.17)(64bit)` 依赖解析失败。

当前 fix 分支上的 Dockerfile 已修复此问题：
1. 新增多阶段构建 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，利用官方 FoundationDB Docker 镜像的多架构支持（已通过 Docker Hub API 验证 `7.3.77` tag 同时提供 amd64 和 arm64 镜像）。
2. 使用 `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` 从官方镜像复制客户端二进制和库文件，BuildKit/Docker 会自动选择与构建平台匹配的架构。
3. FoundationDB 头文件通过独立的 `fdb-headers` tarball 下载（架构无关，压缩包内容仅为 C 头文件）。
4. 添加了 clang 多架构兼容符号链接逻辑，使用 `$(uname -m)` 动态检测架构构造正确的库路径。

此方案彻底消除了 RPM 硬编码架构问题，同时支持 x86_64 和 aarch64 两种构建平台。

## 潜在风险
无。多阶段构建方案依赖 `foundationdb/foundationdb:7.3.77` 官方镜像的多架构支持，已确认该 tag 在 Docker Hub 上同时提供 amd64 和 arm64 manifest，BuildKit 会在构建时自动拉取匹配当前平台的镜像层。