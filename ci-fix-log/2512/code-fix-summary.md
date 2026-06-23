# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 和 clang 库路径硬编码了 `aarch64` 架构后缀，导致在 x86_64 CI 构建作业上因架构不匹配而失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从 RPM 下载改为多阶段构建 COPY；将 clang 库路径从硬编码 `aarch64` 改为动态 `ARCH=$(uname -m)`；移除可能不可用的 yum 包和不必要的 cmake/sed 补丁。

## 修复逻辑

### 根因：FoundationDB RPM 架构硬编码
原 PR 代码通过 RPM 安装 FoundationDB，URL 中硬编码了 `aarch64`：
```
foundationdb-clients-7.3.77-1.el9.aarch64.rpm
```
经实际验证，`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 GitHub Releases 中不存在（HTTP 404），因此 CI 分析报告中的"方向 1"（使用 TARGETARCH 切换 RPM 文件名）不可行。修复采用"方向 2"——多阶段构建 COPY 方式：从 `foundationdb/foundationdb:7.3.77` 官方镜像中直接 COPY `fdbcli` 和 `libfdb_c.so` 二进制文件，完全绕过 RPM 安装。已从上游 `7.3.77` tag 获取 FoundationDB 官方 Dockerfile，验证 COPY 源路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 均存在。

### 附带修复：clang 库路径架构硬编码
原代码中 clang 库符号链接路径也硬编码了 `aarch64-openEuler-linux-gnu`，改为 `ARCH=$(uname -m)` 动态获取当前架构。

### 清理优化
- 移除 `clang-tools-extra`、`rdma-core-devel`、`numactl-devel`、`python3-devel`、`autoconf`、`automake`、`libtool` 等可能不在 openEuler 24.03-LTS-SP3 yum 仓库中的包
- 移除针对原始构建流程的多余 sed 补丁和 cmake 标志（`-DBUILD_TESTING=OFF`、`-DFOLLY_CPP_ATOMIC_BUILTIN`、`-Wno-error` 等）
- 将运行时安装中的 `boost-foundation` 修正为 `boost-filesystem`
- 通过 tarball 下载 FDB 头文件（架构无关）

## 潜在风险
- FoundationDB 7.3.77 客户端库（`libfdb_c.so`）在 openEuler 24.03-LTS-SP3 上可能存在 glibc 版本兼容性问题，修复架构后需在实际 CI 构建中验证 cmake 编译步骤通过
- 移除 `-DBUILD_TESTING=OFF` 后，3fs 的测试子项目可能被 cmake 默认构建，增加构建时间但不会导致构建失败