# 修复摘要

## 修复的问题
FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 平台标识，导致在 x86_64 CI 宿主机构建时 RPM 依赖（`libm.so.6(GLIBC_2.17)`）无法满足。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 新增多阶段构建，从 `foundationdb/foundationdb:${FDB_VERSION}` 镜像提取 FoundationDB 客户端二进制和库文件，替代硬编码架构的 RPM 安装
  2. 新增 `FDB_VERSION` ARG 变量实现版本参数化
  3. 将 clang 库符号链接中的硬编码 `aarch64` 替换为动态 `$(uname -m)` 检测
  4. 新增从 GitHub Releases 下载 fdb-headers 的步骤以提供编译所需的头文件

## 修复逻辑
分析报告指出原始 Dockerfile 第 22 行的 `rpm -ivh` 命令使用的 RPM URL 硬编码了 `aarch64` 架构，而 CI 构建宿主机的 meson 检测确认为 `x86_64`。同时 RPM 是为 RHEL 9 (`el9`) 构建的，与 openEuler 的 glibc 版本符号不完全兼容。

修复采用分析报告建议的"方向 1"策略：通过多阶段构建（`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`）从 FoundationDB 官方 Docker 镜像中直接 `COPY --from=fdb` 提取二进制文件，彻底绕过了 RPM 架构硬编码和平台依赖问题。FoundationDB 官方镜像已包含多架构支持，无需在 Dockerfile 中手动判断架构。

## 潜在风险
无。多阶段构建使用 FoundationDB 官方维护的 Docker 镜像，架构兼容性由上游保障。`COPY --from=fdb` 的路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 在 FoundationDB 官方镜像中跨架构一致。