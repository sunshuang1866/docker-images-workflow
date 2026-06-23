# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构，导致 x86_64 CI 构建失败；同时修复了 `git clone --depth 1` 导致 `git checkout` 静默失败的问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装从架构硬编码的 RPM 下载改为多阶段构建 `COPY --from=fdb`；移除 `git clone --depth 1` 和 `git checkout ... 2>/dev/null || true` 静默失败模式；将 clang 运行时库路径从硬编码 `aarch64` 改为 `$(uname -m)` 动态检测。

## 修复逻辑
CI 分析报告指向的两个根因均已修复：

1. **架构 URL 硬编码**：Dockerfile 原先通过 `rpm -ivh` 安装 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，URL 中硬编码了 `aarch64`。修复方案为使用多阶段构建：`FROM foundationdb/foundationdb:7.3.77 AS fdb` 拉取官方 FoundationDB Docker 镜像（本身已含正确架构的二进制），然后通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`。头文件通过 `curl` 从 GitHub Releases 下载架构无关的 tarball。此方案对 aarch64 和 x86_64 均适用，无需架构判断。

2. **git checkout 静默失败**：原 PR 使用 `git clone --depth 1 --shallow-submodules` 配合 `git checkout ${VERSION} 2>/dev/null || true`，在浅克隆中 checkout 一个不在浅历史中的 commit 时会静默失败，导致构建出错误版本的 3FS 二进制。修复移除了 `--depth 1`（完整克隆）和 `2>/dev/null || true`（让失败显式报错）。

3. **clang 路径硬编码**（附加修复）：原先 clang 运行时库路径硬编码 `aarch64-openEuler-linux-gnu`，改为 `ARCH=$(uname -m)` 动态拼接，使构建在两种架构上均能正确链接。

## 潜在风险
- 完整 `git clone`（无 `--depth 1`）会占用更多网络带宽和磁盘空间，但 3FS 仓库规模有限，风险可控。
- `COPY --from=fdb` 依赖 `foundationdb/foundationdb:7.3.77` 镜像在 Docker Hub 上可用，若该镜像不可达则构建会显式失败（而非静默跳过），这是预期行为。