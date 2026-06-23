# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端安装硬编码了 `aarch64` 架构的 RPM URL，导致 x86_64 构建环境跨架构安装失败。同时修复了浅克隆（`--depth 1`）与指定 commit hash 不兼容的问题，以及 clang 库路径中硬编码的 `aarch64` 架构。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 将 FoundationDB 安装从硬编码 `aarch64` RPM 下载安装，改为多阶段构建：从 `foundationdb/foundationdb:${FDB_VERSION}` 官方多架构镜像中 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`
  - 移除 `git clone` 的 `--depth 1` 参数，避免浅克隆无法 checkout 指定 commit hash
  - 将 clang 库路径中硬编码的 `aarch64` 替换为 `ARCH=$(uname -m)` 动态推导

## 修复逻辑
CI 分析报告的根因是 `Dockerfile:22-24` 行中 `curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh` 硬编码了 aarch64 架构，与 CI 的 x86_64 构建环境不兼容。修复方案采用分析报告中的"方向 2"（置信度：中）：改用 FoundationDB 官方多架构 Docker 镜像的多阶段构建方案。已从上游 `7.3.77` tag 获取 FoundationDB Dockerfile 验证，`/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径存在且正确，官方镜像已使用 `TARGETARCH` 支持多架构。

同时修复了分析报告"需要进一步确认的点"中提到的模式18：`--depth 1` 浅克隆与 `git checkout ${VERSION}`（VERSION 为 commit hash 前 7 位）不兼容——`--depth 1` 只包含最新提交，其他 commit hash 可能不可达。移除 `--depth 1` 后使用完整克隆。

clang 库路径中 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/` 的 `aarch64` 也已替换为 `${ARCH}` 变量，通过 `uname -m` 动态推导，确保跨架构兼容。

## 潜在风险
- 多阶段构建依赖 `foundationdb/foundationdb:7.3.77` 镜像的可用性——该镜像已在 Docker Hub 上发布且支持 amd64/arm64 多架构，风险较低
- 移除 `--depth 1` 后 `git clone --recurse-submodules` 会下载完整仓库历史，增加构建时间和网络消耗，但不影响构建正确性