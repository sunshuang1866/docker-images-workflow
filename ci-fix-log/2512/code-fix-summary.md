# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构，在 x86_64 CI 构建环境中导致 `rpm -ivh` 安装失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端安装方式从 RPM 下载安装改为多阶段构建 COPY 方式，同时将 clang 库路径从硬编码 `aarch64` 改为架构感知。

## 修复逻辑
按照 CI 分析报告「方向 2」建议，采用多阶段构建方案：
1. 新增 `ARG FDB_VERSION=7.3.77` 和 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 阶段，利用 Docker 多架构镜像能力自动拉取与构建环境匹配的 FoundationDB 镜像
2. 将原来的 `RUN ARCH=$(uname -m) ... curl ... rpm -i ...` 替换为 `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so`，直接复用官方镜像中的预编译二进制
3. 补充 FoundationDB C API 头文件下载（`fdb-headers` tarball），确保 3FS 编译期能找到 FoundationDB 头文件
4. 将 clang 库符号链接路径中硬编码的 `aarch64` 替换为 `ARCH=$(uname -m)` 动态检测，消除跨架构构建障碍

已从上游 `foundationdb/foundationdb:7.3.77` 对应 tag 的 `packaging/docker/Dockerfile` 获取源文件验证，确认 `fdbcli` 位于 `/usr/bin/fdbcli`、`libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，COPY 路径匹配成功。

## 潜在风险
- `libfdb_c.so` 从 Rocky Linux 9.4 基础镜像中提取，其 glibc/gcc 运行时依赖（libstdc++、libgcc_s）需在 openEuler 24.03 上可用，当前 yum 安装步骤中已包含 gcc-c++，相关运行时库应存在
- 若 FoundationDB 7.3.77 的 `foundationdb/foundationdb` 镜像未来废弃或变更内部路径，需同步更新 COPY 指令