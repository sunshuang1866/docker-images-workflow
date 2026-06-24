# 修复摘要

## 修复的问题
FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构标识，导致 x86_64 构建在安装 aarch64 架构 RPM 包时依赖解析失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除硬编码架构的 FoundationDB RPM 安装方式，改用多阶段构建从 `foundationdb/foundationdb` 官方 Docker 镜像 `COPY --from=fdb` 获取客户端二进制和库文件；同时将 clang 运行时库的符号链接路径从硬编码 `aarch64` 改为动态 `ARCH=$(uname -m)`；新增架构无关的 FoundationDB 头文件下载步骤。

## 修复逻辑
CI 失败的直接原因是原 Dockerfile 中 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 的 URL 将架构写死为 `aarch64`，在 x86_64 CI 节点上 `rpm -ivh` 安装 aarch64 包时无法在 x86_64 glibc 中找到 aarch64 所需的 `libm.so.6(GLIBC_2.17)(64bit)` 能力，导致依赖解析失败。

修复方案采用 CI 分析报告"方向 2"的思路：不再通过 RPM 安装 FoundationDB 客户端，而是利用多阶段构建从 `foundationdb/foundationdb:7.3.77` 官方镜像（该镜像支持多架构 manifest，Docker/BuildKit 会自动拉取正确架构的镜像层）中 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`。同时保留架构无关的头文件 tarball 下载用于编译链接。clang 运行时符号链接中的硬编码 `aarch64` 也一并改为 `$(uname -m)` 动态获取。

## 潜在风险
- `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` 在运行时可能依赖 FoundationDB 基础镜像中的特定 glibc 版本或其他共享库，如 openEuler 24.03 的 glibc 版本与之不兼容，3FS 运行时加载 `libfdb_c.so` 可能出现符号缺失。此为运行时风险，不影响镜像构建成功。
- `foundationdb/foundationdb` 官方镜像是必要的构建依赖，若 Docker Hub 不可达则构建失败。