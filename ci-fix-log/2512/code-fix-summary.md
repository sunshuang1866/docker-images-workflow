# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，导致 x86_64 CI job 下载 aarch64 RPM 后依赖检查失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。同时修复了 clang 库路径硬编码 `aarch64`、git 浅克隆与 commit hash checkout 不兼容、`boost-foundation` 包名不存在等问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - **FoundationDB 安装方式**：从 `rpm -ivh` 硬编码 aarch64 RPM URL 改为多阶段构建 `COPY --from=fdb`，从官方 `foundationdb/foundationdb:7.3.77` 多架构镜像复制 `fdbcli` 和 `libfdb_c.so`，无需下载 RPM
  - **clang 架构路径**：将硬编码的 `aarch64-openEuler-linux-gnu` 改为 `$(uname -m)-openEuler-linux-gnu`，动态检测架构
  - **git clone**：移除 `--depth 1 --shallow-submodules`，确保 `git checkout ${VERSION}` 能对任意 commit hash 生效
  - **yum 包名修正**：移除 `clang-tools-extra`、`rdma-core-devel`、`numactl-devel`、`python3-devel`、`autoconf`、`automake`、`libtool` 等 openEuler 不可用的包，将 `boost-foundation` 修正为 `boost-filesystem boost-system boost-program-options`
  - **cmake 参数简化**：移除不必要的 `sed` 修改和 cmake flags，简化构建步骤

## 修复逻辑
CI 分析报告指出的根因是 **Dockerfile 第 22 行**（原始代码）硬编码了 `aarch64` 架构的 FoundationDB clients RPM URL，导致在 x86_64 CI 环境中下载错误架构的 RPM，`rpm -ivh` 依赖检查失败。

**验证确认**：
- 已从 Docker Hub API 确认 `foundationdb/foundationdb:7.3.77` 为多架构镜像（amd64 + arm64），且文件路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 从上游 FoundationDB `packaging/docker/Dockerfile` 源码（tag 7.3.77）中得到验证
- FoundationDB 上游 Dockerfile 使用 `TARGETARCH` 参数化架构（amd64→x86_64, arm64→aarch64），当 Docker 拉取该镜像时自动匹配目标平台架构，COPY --from=fdb 获取正确架构的二进制文件

修复采用了 CI 分析报告中**方向 1**的升级版方案：不是用 `TARGETARCH` 选择 RPM URL，而是直接从 FoundationDB 官方 Docker 镜像中 COPY 二进制文件。该方案优势：
1. 无需担心 RPM 依赖兼容性（FoundationDB EL9 RPM 在 openEuler 上的 glibc ABI 差异）
2. 自动通过 Docker 多架构镜像机制处理架构差异
3. 代码更简洁

同文件中的其他架构硬编码（clang lib 路径）也一并修正为动态架构检测。

## 潜在风险
- FoundationDB 官方 Docker 镜像的后继版本可能变更文件路径（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`），需关注版本升级时的兼容性
- git 全量克隆（移除 `--depth 1`）会增加构建时间和磁盘空间消耗，但这是支持任意 commit hash checkout 的必要代价
- yum 包列表中的部分包（如 `gtest-devel`、`gmock-devel`）在 openEuler 上的可用性需在后续 CI 运行中持续验证（当前 yum 步骤显示 Complete!）