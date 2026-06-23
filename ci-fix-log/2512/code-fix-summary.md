# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构，导致 x86_64 平台上构建失败（依赖解析错误）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从硬编码架构的 RPM 下载安装改为多阶段构建（multi-stage build），从官方 `foundationdb/foundationdb` 镜像（支持 amd64/arm64 双架构）复制所需二进制和库文件。

## 修复逻辑

**根因**：CI 分析报告指出，Dockerfile 第 22-24 行的 FoundationDB RPM 下载 URL 中硬编码了 `aarch64` 架构名，未做架构检测，导致在 x86_64 构建机上尝试安装 aarch64 架构的 RPM 失败。

**修复方式**（已通过 `fix/2512` 分支上的多次提交完成）：
1. 在 Dockerfile 顶部声明 `ARG FDB_VERSION=7.3.77` 并在第一个 `FROM` 之前使用，创建 `fdb` 构建阶段：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`
2. 在主构建阶段通过 `COPY --from=fdb` 复制 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so`，无需下载 RPM
3. 保留 FDB 头文件的单独下载（`fdb-headers-${FDB_VERSION}.tar.gz`，架构无关）

**验证结果**：
- 已确认 `foundationdb/foundationdb:7.3.77` 在 Docker Hub 上同时提供 `amd64` 和 `arm64` 两种架构的镜像
- 已从上游 `release-7.3` 分支获取 FoundationDB Dockerfile 验证，确认官方镜像中文件路径为 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so`（与架构无关），`COPY --from=fdb` 使用的源路径正确

此修复通过多阶段构建从根本上消除了 RPM 架构适配问题，优于仅将 RPM URL 中架构名动态化（因为后者还可能在 openEuler 上遇到 RPM 依赖冲突）。

## 潜在风险
- `foundationdb/foundationdb:7.3.77` 基于 RockyLinux 9.4-minimal 构建，`libfdb_c.so` 链接的 glibc 版本（2.34）低于 openEuler 24.03-LTS-SP3（约 2.38），由于 glibc 向后兼容，理论无兼容性问题，但需在 CI 中实际验证
- 若 FoundationDB 未来版本更改了 Docker 镜像内的文件布局，`COPY --from=fdb` 的源路径可能需要调整