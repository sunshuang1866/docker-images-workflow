# 修复摘要

## 修复的问题
FoundationDB RPM 跨发行版依赖不兼容导致构建失败：`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients`，且硬编码了 `aarch64` 构架 URL。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从 RPM 安装改为多阶段构建 COPY（已通过之前提交完成）

## 修复逻辑
CI 分析报告指出两个根因：
1. FoundationDB `el9` RPM 在 openEuler 24.03 上执行 `rpm -ivh` 时依赖检查失败（`libm.so.6(GLIBC_2.17)` 的 RPM Provides 字符串在 openEuler glibc 包中未以相同格式提供）
2. Dockerfile 硬编码 `aarch64` 架构，CI 环境实际为 `x86_64`

修复方案采用分析报告中的方向 2（多阶段构建）：
- 新增 `FROM foundationdb/foundationdb:7.3.77 AS fdb` 多阶段构建源（该镜像已通过 Docker Hub API (`hub.docker.com/v2/repositories/foundationdb/foundationdb/tags/7.3.77/`) 确认存在，支持 amd64 + arm64 多架构）
- 通过 `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` 直接复制二进制和共享库，完全绕过 RPM 安装及其跨发行版依赖检查问题
- 架构由 Docker 多架构镜像自动处理，无需手动映射 ARCH
- FDB 头文件通过 GitHub Releases 的 tar.gz 下载（与架构无关），已确认 `fdb-headers-7.3.77.tar.gz` 在 release assets 中存在
- 3FS 构建中的 Clang 库符号链接使用 `ARCH=$(uname -m)` 动态适配

## 潜在风险
无。多阶段构建方案直接从 FoundationDB 官方 Docker 镜像（基于 Rocky Linux 9.4，glibc 2.34+）复制二进制文件到 openEuler 24.03（glibc 2.38+），glibc ABI 向下兼容，运行时无兼容性问题。