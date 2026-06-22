# 修复摘要

## 修复的问题
FoundationDB RPM 包在 openEuler 24.03 上因 glibc 符号版本不兼容导致依赖检查失败，构建中断。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 改用多阶段构建从 FoundationDB 官方 Docker 镜像提取客户端二进制，替代 RPM 下载安装方式

## 修复逻辑

采用 CI 分析报告推荐的方向 1（高置信度）——多阶段构建绕过 RPM 依赖冲突。

**具体改动：**
1. 将 `ARG FDB_VERSION=7.3.77` 提升到第一个 `FROM` 之前（全局 ARG），使其可用于 fdb 镜像拉取
2. 新增第一阶段：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，拉取 FoundationDB 官方镜像（支持 amd64/arm64 双架构，Docker 自动选择匹配平台）
3. 移除原有的 RPM 下载/安装步骤（原第 22-26 行），替换为 `COPY --from=fdb` 直接复制二进制文件和库：
   - `/usr/bin/fdbcli` → 客户端CLI
   - `/usr/lib/libfdb_c.so` → `/usr/lib64/libfdb_c.so`（C 客户端库，放在标准库路径供 3FS cmake 链接）

**为什么这样修复有效：**
- CI 失败根因是 FoundationDB 为 RHEL9/CentOS9 构建的 `.rpm` 包声明了 `libm.so.6(GLIBC_2.17)(64bit)` 依赖，而 openEuler 24.03 的 glibc 采用不同的符号版本管理方案，无法满足该 RPM 的依赖声明
- FoundationDB 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`，基于 Rocky Linux 9.4）不使用 RPM，而是直接从 GitHub Releases 下载 raw 二进制文件（`fdbcli.x86_64`、`libfdb_c.x86_64.so` 等），完全绕过了 RPM 的依赖检测机制
- 已通过 HEAD 请求验证 FoundationDB 7.3.77 的 raw 二进制文件在 GitHub Releases 上对 x86_64 和 aarch64 两种架构均可用（HTTP 200）
- Docker 多阶段构建会自动根据构建平台拉取匹配的 FoundationDB 镜像（linux/amd64 或 linux/arm64），正确选择对应架构的二进制文件

## 潜在风险
- 从 FoundationDB 官方镜像复制的二进制文件基于 Rocky Linux 9.4 构建，虽然绕过 RPM 检测，但运行时仍需 openEuler 24.03 的 glibc 提供兼容的符号。FoundationDB 的二进制文件通常静态链接大部分依赖或使用受限的 glibc 符号集，在 openEuler 上直接运行的概率高，但未在 openEuler 24.03 环境中测试过实际的 `ldd /usr/bin/fdbcli` 结果。
- 需要确认 3FS cmake 构建时能在 `/usr/lib64/` 路径下找到 `libfdb_c.so`（该路径是 x86_64 Linux 的标准库路径）。