# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端安装 URL 硬编码为 `aarch64` 架构，导致 x86_64 CI 构建时 `rpm -ivh` 因架构不匹配而失败。同时修复了浅克隆 git checkout 静默失败隐患和 clang 符号链接架构硬编码问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 将 FoundationDB 客户端 RPM 安装替换为 `COPY --from=fdb`（从官方 `foundationdb/foundationdb:${FDB_VERSION}` 镜像提取二进制），消除架构依赖
  2. 新增 `ARG FDB_VERSION=7.3.77` 在第一个 `FROM` 前，使 FoundationDB 镜像版本可配置
  3. 将 git clone 从浅克隆（`--depth 1` + `|| true`）改为完整克隆，确保 `checkout ${VERSION}` 可靠执行
  4. 将 clang 库符号链接从硬编码 `aarch64` 改为 `${ARCH}` 运行时检测
  5. 新增 FDB 头文件下载（`fdb-headers-${FDB_VERSION}.tar.gz`），架构无关

## 修复逻辑
分析报告指出根因为 Dockerfile 中 FoundationDB 7.3.77 RPM URL 硬编码为 `aarch64`（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），在 x86_64 上必然失败。采用分析报告方向 2（从 FoundationDB 官方 Docker 镜像 `COPY --from` 提取二进制），该方案完全绕开 RPM 架构匹配问题——Docker BuildKit 在拉取 `foundationdb/foundationdb` 镜像时会自动选择与构建目标架构匹配的镜像，二进制文件天然适配。同时一并修正了分析报告指出的 git 浅克隆 + `|| true` 隐患（模式 18），改为完整克隆确保 checkout 不会静默失败。

## 潜在风险
- FoundationDB 头文件需要通过 GitHub Releases 下载（`fdb-headers-${FDB_VERSION}.tar.gz`），若 GitHub 不可达则此步骤失败。这是架构无关的下载，不构成架构兼容性风险。
- `COPY --from=fdb` 依赖上游 `foundationdb/foundationdb` Docker 镜像中 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径稳定存在，若上游镜像结构变更需同步更新。