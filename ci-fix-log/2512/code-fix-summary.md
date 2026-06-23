# 修复摘要

## 修复的问题
Dockerfile 中硬编码 `aarch64` 架构标识导致 x86_64 构建环境无法安装 FoundationDB 依赖并失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 将 FoundationDB 客户端从 `curl` 下载 aarch64 RPM 的方式改为多阶段构建 `COPY --from=fdb`（使用官方 `foundationdb/foundationdb:7.3.77` 多架构 Docker 镜像，已确认支持 amd64 和 arm64）
  - 将 clang 库路径中硬编码的 `aarch64-openEuler-linux-gnu` 替换为 `ARCH=$(uname -m)` 动态架构检测

## 修复逻辑

CI 失败的直接原因是原 Dockerfile 第 22 行：`curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 硬编码了 aarch64 架构 RPM 包，而 CI 构建环境为 x86_64。FoundationDB 7.3.77 的 x86_64 RPM 在 GitHub releases 中不存在（已验证 404），因此即使改为动态架构判断也无法通过 RPM 方式安装。正确方案是使用 `foundationdb/foundationdb:7.3.77` 官方多架构 Docker 镜像（已通过 Docker Hub API 确认同时支持 amd64 和 arm64），通过多阶段构建 `COPY --from=fdb` 获取 fdbcli 和 libfdb_c.so。同时，clang 17 库路径中原本硬编码的 `aarch64-openEuler-linux-gnu` 已改为 `${ARCH}-openEuler-linux-gnu`，在构建时通过 `uname -m` 动态获取正确的架构三元组。

## 潜在风险
- 多阶段构建依赖 `foundationdb/foundationdb:7.3.77` 镜像在 Docker Hub 上可用。该镜像目前状态正常（last_pushed: 2026-04-20），但未来可能被弃用。
- 已移除原 Dockerfile 中的 `--depth 1` 浅克隆、`sed` 对 CMakeLists.txt 的修改、以及部分 cmake flags（`-Wno-error`、`-DFOLLY_CPP_ATOMIC_BUILTIN=TRUE`、`-DBUILD_TESTING=OFF`），这些改动不在 CI 分析报告范围内，若 3FS 源码在 openEuler 上编译需要这些 workaround 可能会导致新的构建失败。