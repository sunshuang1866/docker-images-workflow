# 修复摘要

## 修复的问题
FoundationDB 客户端安装使用 EL9 架构的 RPM 包导致 `libm.so.6(GLIBC_2.17)` 依赖在 openEuler 上不满足，构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除 RPM 安装方式，改为多阶段构建从 `foundationdb/foundationdb:7.3.77` 官方镜像直接 COPY 二进制文件和共享库。

## 修复逻辑
1. **根因**：CI 分析报告指出 Dockerfile 使用了 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`（硬编码 `aarch64` + `el9`），导致 `rpm -ivh` 在 openEuler 上因 glibc 符号版本差异而依赖检查失败。
2. **修复方案**：采用多阶段构建，通过 `FROM foundationdb/foundationdb:7.3.77 AS fdb` 引入 FoundationDB 官方镜像（多架构，支持 amd64 和 arm64），然后用 `COPY --from=fdb` 从该镜像中提取 `fdbcli` 和 `libfdb_c.so`。FoundationDB 官方镜像中的二进制文件为直接从 GitHub Release 下载的原始 ELF 可执行文件（非 RPM 打包），完全绕过了 RPM 依赖检查问题。
3. **验证结果**：
   - FoundationDB 7.3.77 Docker 镜像确认存在且为多架构（amd64 + arm64），参见 hub.docker.com 标签 API 返回
   - FoundationDB 7.3.77 GitHub Release 包含 `fdb-headers-7.3.77.tar.gz`（用于头文件下载），以及各架构的二进制文件（`fdbcli.x86_64`、`fdbcli.aarch64` 等）
   - FoundationDB 官方 Dockerfile（来自上游 `7.3.77` tag）证实 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径存在
4. **补充修复**（已在先前迭代中完成）：
   - 移除了 `git clone --depth 1` 以避免浅克隆导致的 checkout 失败
   - 添加了 `ARCH=$(uname -m)` 动态架构符号链接以修复 clang 库路径问题
   - 添加了 FoundationDB 头文件下载步骤
   - 修正了 `boost-foundation` 包名错误为 `boost-filesystem`

## 潜在风险
无。当前方案使用 FoundationDB 官方 Docker 镜像中已经验证过的二进制文件，不涉及 RPM 依赖解析，且官方镜像为多架构自动匹配构建目标架构。