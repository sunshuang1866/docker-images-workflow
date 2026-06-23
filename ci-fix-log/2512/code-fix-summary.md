# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64`，在 x86_64 平台构建时因架构不匹配导致 `rpm -ivh` 失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从 RPM 硬编码 aarch64 架构改为多阶段构建 `COPY --from=fdb`（从 `foundationdb/foundationdb:7.3.77` 官方镜像复制 fdbcli 和 libfdb_c.so）；同时将 clang 库路径和 libclang_rt.builtins 文件名从硬编码 `aarch64` 改为使用 `ARCH=$(uname -m)` 动态适配。

## 修复逻辑
CI 分析报告指出根因是原 Dockerfile 第 22 行 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 硬编码了 aarch64 架构。修复采用分析报告中的"方向 2"——使用 FoundationDB 官方 Docker 镜像的多阶段构建方案：通过 `FROM foundationdb/foundationdb:7.3.77 AS fdb` 拉取架构正确的官方镜像，再用 `COPY --from=fdb` 复制 fdbcli 和 libfdb_c.so。该方案天然支持多架构（Docker 会自动拉取匹配的镜像变体），无需手动检测架构或拼接 URL。同时将原 Dockerfile 中其他硬编码的 aarch64 路径（clang 库路径、libclang_rt.builtins 链接）改为 `$(uname -m)` 动态值，确保 x86_64 和 aarch64 平台均可构建。

## 潜在风险
无。多阶段构建从官方 `foundationdb/foundationdb` 镜像复制二进制文件，该镜像同时提供 x86_64 和 aarch64 架构，且版本由统一 `ARG FDB_VERSION=7.3.77` 控制，不会引入版本不一致问题。