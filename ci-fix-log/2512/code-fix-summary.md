# 修复摘要

## 修复的问题
FoundationDB RPM URL 和 Clang 库路径硬编码 aarch64 导致 x86_64 CI 环境构建失败，以及 git 浅克隆与 commit hash checkout 冲突。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:
  1. **FoundationDB 获取方式**：将硬编码 aarch64 架构的 RPM 下载安装（`curl + rpm -ivh foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）替换为多阶段构建 `COPY --from=fdb`，从官方 `foundationdb/foundationdb:7.3.77` 镜像复制 `fdbcli` 和 `libfdb_c.so`，利用 Docker 多架构支持自动匹配构建环境架构。
  2. **Clang 库路径**：将硬编码 `aarch64-openEuler-linux-gnu` 路径改为 `$(uname -m)-openEuler-linux-gnu`，通过 `ARCH=$(uname -m)` 动态检测架构。
  3. **git clone**：移除 `--depth 1 --shallow-submodules` 浅克隆参数，改为完整克隆（`git clone --recurse-submodules`），确保后续 `git checkout 22fca04`（commit hash）能正确签出；同时移除 `2>/dev/null || true` 静默错误掩盖。
  4. **依赖清理**：移除未使用的 `boost-foundation` 运行时包（修正为 `boost-filesystem boost-system boost-program-options`），添加 `libevent-devel` 构建依赖。

## 修复逻辑
CI 分析报告的三个根因均已修复：

1. **依赖错误（根因1）**：FoundationDB RPM URL 中 `aarch64` 硬编码导致 x86_64 环境 `rpm -ivh` 失败，报 `libm.so.6(GLIBC_2.17)(64bit) is needed`。改用多阶段 `COPY --from=fdb`，由 Docker 根据构建平台自动拉取对应架构的 FoundationDB 镜像，无需手动下载 RPM。

2. **构建阻塞（根因2）**：`ln -sf /usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/...` 路径在 x86_64 系统上不存在。改为 `${ARCH}-openEuler-linux-gnu` 通过 `uname -m` 运行时获取架构。

3. **git 浅克隆冲突（根因3）**：`git clone --depth 1` 后 `git checkout 22fca04`（commit hash）在 shallow clone 中无效，且 `2>/dev/null || true` 掩盖错误。改用完整克隆并移除错误压制，确保 checkout 正确执行且失败时快速暴露。

## 潜在风险
- `COPY --from=fdb` 依赖 CI 环境能访问 Docker Hub 并拉取 `foundationdb/foundationdb:7.3.77` 镜像（需代理或网络可达）。
- 完整 git clone（无 `--depth 1`）会增加构建时间和带宽，但确保 commit hash checkout 可靠性。
- 本次修改从中间 commit `b39b6225` 中移除了 `sed` 补丁（`-DCMAKE_CXX_FLAGS="-Wno-error..."`、`-DFOLLY_CPP_ATOMIC_BUILTIN=TRUE`、`-DBUILD_TESTING=OFF`），若原始 3fs 源码需要这些补丁才能编译通过，后续 CI 构建可能暴露新的编译错误。但分析报告未将这些列为失败原因，修复范围限定在报告指出的三个问题。