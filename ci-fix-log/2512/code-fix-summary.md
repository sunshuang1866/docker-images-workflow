# 修复摘要

## 修复的问题
将 FoundationDB clients 的安装方式从 RPM 包安装（`rpm -i`）改为多阶段构建（`COPY --from=fdb`），消除跨发行版 RPM 依赖不兼容导致的构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除 `curl + rpm -i` 安装 FDB RPM 的命令，改为多阶段构建，从官方 `foundationdb/foundationdb:7.3.77` 镜像中直接复制 `fdbcli` 和 `libfdb_c.so` 二进制文件，并从 GitHub Release 下载头文件归档。

## 修复逻辑

**根因**: 原始 Dockerfile 使用 `rpm -i --nodeps --noscripts` 安装 FoundationDB 的 `el9.aarch64` RPM 包。该 RPM 声明了 `libm.so.6(GLIBC_2.17)` 版本化依赖，在 openEuler 24.03 的 glibc 中无法解析；且硬编码为 aarch64 架构，与 CI 实际构建环境（x86_64）不匹配。

**修复方案**: 采用多阶段构建：
1. 前置一个 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 阶段，利用 Docker 自动选择匹配构建架构的镜像变体（amd64/arm64）
2. 用 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so` 直接复制预编译的 FDB 客户端二进制文件，完全绕过 RPM 依赖解析
3. 从 GitHub Release 下载 `fdb-headers-${FDB_VERSION}.tar.gz` 提供编译所需的 C API 头文件

**验证结果**:
- 已从 Docker Hub API 确认 `foundationdb/foundationdb:7.3.77` 镜像存在，提供 amd64 和 arm64 两种架构变体
- 已从 GitHub Release API 确认 `fdb-headers-7.3.77.tar.gz` 制品存在，URL 格式正确
- 已从 FoundationDB 官方 Dockerfile（`release-7.3` 分支）确认 `libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，`fdbcli` 位于 `/usr/bin/fdbcli`
- `--depth 1` + commit hash checkout 问题（模式 18）：当前 Dockerfile 使用完整 `git clone`（无 `--depth 1`），不存在此问题

## 潜在风险
- FoundationDB 官方 Docker 镜像基于 Rocky Linux 9.4，其预编译的 `libfdb_c.so` 在 openEuler 24.03 上运行时可能存在 libc++ 等运行时库版本差异，但不影响 Docker 构建过程本身
- 若 FoundationDB 7.3.77 镜像从 Docker Hub 移除或架构支持变更，构建将失败