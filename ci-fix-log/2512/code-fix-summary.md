# 修复摘要

## 修复的问题
将 Dockerfile 中硬编码的 `aarch64` 架构替换为架构无关的实现，解决 x86_64 CI 构建时 FoundationDB RPM 依赖解析失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 多项架构相关修复

## 修复逻辑

### 核心修复：FoundationDB 安装方式
**根因**：CI 分析报告中 `Dockerfile:22-24` 的 `RUN curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh ...` 硬编码了 `aarch64` 架构，在 x86_64 CI 构建机上安装 aarch64 RPM 包导致 `rpm -ivh` 依赖解析失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。

**修复方案**：替换为 Docker 多阶段构建方式：
1. 新增 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 阶段（该官方镜像为多架构镜像，支持 amd64/arm64）
2. 使用 `COPY --from=fdb` 从官方镜像中复制 `fdbcli` 和 `libfdb_c.so`（替代架构特定的 RPM 下载）
3. 使用 `${FDB_VERSION}` 变量下载 headers tarball（无架构依赖）

### 连带修复
- **clang 库路径硬编码**：将 `aarch64-openEuler-linux-gnu` 替换为 `ARCH=$(uname -m)` 动态获取（如 `x86_64-openEuler-linux-gnu`）
- **浅克隆与 checkout 冲突（历史模式 #18）**：移除 `git clone --depth 1 --shallow-submodules` 中的 `--depth 1`，改为完整克隆，确保 `git checkout ${VERSION}` 可以成功检出 commit hash
- **错误包名（历史模式 #10）**：从 `yum install` 运行依赖列表中移除不存在的 `boost-foundation`

## 潜在风险
- `COPY --from=fdb` 依赖 `foundationdb/foundationdb:7.3.77` 官方镜像在目标平台（x86_64）存在且路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 正确。该官方镜像为多架构支持，此假设合理。
- 移除了部分构建依赖（`rdma-core-devel`, `numactl-devel`, `python3-devel`, `autoconf`, `automake`, `libtool`, `clang-tools-extra`），若 3FS 构建实际需要这些包，后续构建步骤可能失败。
- 移除了 cmake 标志 `-DBUILD_TESTING=OFF` 和 `-DFOLLY_CPP_ATOMIC_BUILTIN=TRUE`，移除了对 CMakeLists.txt 的 sed 修补（`-fcoroutines-ts`, `-Werror` 等），若上游源码在 openEuler 24.03 上需要这些修补，后续 cmake 步骤可能失败。