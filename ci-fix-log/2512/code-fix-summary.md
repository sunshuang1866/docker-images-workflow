# 修复摘要

## 修复的问题
将 FoundationDB RPM 安装改为从官方 Docker 镜像多阶段 COPY 二进制文件，同时移除 git 浅克隆以确保 commit hash checkout 可用，将硬编码的 aarch64 架构改为动态检测。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:
  1. 新增 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建
  2. 将 `rpm -ivh foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 替换为 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so`
  3. 将 FoundationDB headers 下载改为参数化版本 `${FDB_VERSION}`
  4. 移除 `git clone --recurse-submodules --depth 1 --shallow-submodules` 中的 `--depth 1` 和 `--shallow-submodules`
  5. 移除 git checkout 和 submodule update 的 `2>/dev/null || true` 错误抑制
  6. 将 `aarch64-openEuler-linux-gnu` 硬编码替换为 `${ARCH}-openEuler-linux-gnu`，其中 `ARCH=$(uname -m)`

## 修复逻辑

### 根因 1: RPM 依赖失败
原 Dockerfile 硬编码了 aarch64 平台的 `.el9` FoundationDB RPM URL，该 RPM 声明了 `GLIBC_2.17` 版本化符号依赖，openEuler 的 rpm 依赖解析器无法匹配，导致安装失败。

**修复方案**：采用 CI 分析报告推荐的「方向 1」（置信度：高），使用多阶段构建直接从 `foundationdb/foundationdb:7.3.77` 官方容器镜像 COPY 客户端二进制文件（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`）。此方式完全绕过 RPM 依赖解析。已验证：
- Docker Hub 上 `foundationdb/foundationdb:7.3.77` 存在且提供 amd64 + arm64 双架构镜像
- GitHub Release 上 `fdb-headers-7.3.77.tar.gz` 可正常下载

### 根因 2: git 浅克隆与 commit hash checkout 不兼容
原 Dockerfile 使用 `git clone --depth 1`（浅克隆），随后尝试 `git checkout ${VERSION}`（commit hash `22fca04`），浅克隆缺少完整历史导致 checkout 可能失败。且原代码使用 `2>/dev/null || true` 静默忽略错误，可能使构建在错误代码上继续执行。

**修复方案**：移除 `--depth 1` 和 `--shallow-submodules`，改为完整克隆，确保 commit hash checkout 可用。同时移除 `2>/dev/null || true` 错误抑制，确保失败时构建正确停止。

### 根因 3: 架构硬编码
原 Dockerfile 将 clang 库路径硬编码为 `aarch64-openEuler-linux-gnu`，与 CI 构建主机（x86_64）不匹配。

**修复方案**：使用 `ARCH=$(uname -m)` 动态检测架构，以 `${ARCH}-openEuler-linux-gnu` 替换硬编码路径。

## 潜在风险
- 从 Ubuntu 系 FoundationDB 镜像 COPY 的二进制文件（libfdb_c.so）可能与 openEuler 的 glibc 版本存在运行时兼容性差异。CI 分析报告已评估此风险并给出「高」置信度的修复推荐。如实际构建中遇到运行时 glibc 问题，可考虑在 openEuler 上重新编译 FoundationDB 客户端库。