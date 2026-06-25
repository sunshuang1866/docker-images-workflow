# 修复摘要

## 修复的问题
FoundationDB RPM 包在 openEuler 24.03 上因 `libm.so.6(GLIBC_2.17)(64bit)` RPM 元数据依赖不匹配导致 `rpm -ivh` 安装失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端安装方式从 `rpm -ivh` 直接安装 el9 RPM 改为多阶段构建 `COPY --from=fdb`，从官方 FoundationDB Docker 镜像提取二进制文件，并单独下载头文件包。

## 修复逻辑
采用 CI 分析报告方向 2（使用 FoundationDB 官方二进制而非 RPM）的变体方案：利用 FoundationDB 官方发布的多架构 Docker 镜像 `foundationdb/foundationdb:7.3.77` 作为构建阶段，通过 `COPY --from=fdb` 直接提取 `fdbcli` 和 `libfdb_c.so` 二进制文件。头文件则从 GitHub Release 的 `fdb-headers` tarball 单独下载。此方案完全绕过了 RPM 依赖解析，彻底消除了 `libm.so.6(GLIBC_2.17)` 依赖不匹配问题。FoundationDB 官方 Docker 镜像为多架构（amd64/arm64）构建，其二进制文件已针对 aarch64 编译，与 openEuler 24.03 容器环境兼容。

## 潜在风险
FoundationDB Docker 镜像未来版本可能更改内部文件路径（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`），若上游变更需同步更新 `COPY --from=fdb` 的源路径。当前 7.3.77 版本路径已验证正确。