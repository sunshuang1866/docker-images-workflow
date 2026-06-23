# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构，导致 x86_64 CI 构建节点上 rpm 依赖检查失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 的 RPM 安装方式替换为多阶段构建（`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb`），移除硬编码架构的 RPM 下载。同时移除 git clone 的 `--depth 1` 浅克隆选项以避免与 commit hash checkout 不兼容，补回 FoundationDB headers 下载，并将 clang 运行时库路径从硬编码 `aarch64` 改为动态 `ARCH=$(uname -m)`。

## 修复逻辑
CI 分析报告指出行 22-24 的 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` URL 硬编码了 `aarch64` 架构，在 x86_64 构建环境下 rpm 报告 `libm.so.6(GLIBC_2.17)(64bit) is needed` 依赖错误。该问题已在当前分支的先前修复提交中解决：

1. **架构问题（修复方向 1）**：不再通过 RPM 直接安装 FoundationDB clients，改为从 `foundationdb/foundationdb:${FDB_VERSION}` 官方镜像多阶段构建，通过 `COPY --from=fdb` 复制 `fdbcli` 和 `libfdb_c.so`，彻底避免架构匹配和 glibc 兼容性问题。
2. **headers 缺失**：补充了 `fdb-headers` 的下载步骤（架构无关的 tar.gz 包）。
3. **模式 18（git 浅克隆）**：移除了 `git clone --depth 1`，避免浅克隆与特定 commit hash checkout 不兼容。
4. **clang 路径**：将 `aarch64-openEuler-linux-gnu` 硬编码路径改为 `${ARCH}-openEuler-linux-gnu` 动态获取。

当前 Dockerfile 中不再包含任何硬编码 `aarch64` 的 FoundationDB RPM 引用，`grep -n "aarch64\|rpm\|fdb-clients"` 确认无匹配。

## 潜在风险
- `COPY --from=fdb /usr/lib/libfdb_c.so` 的源路径依赖 FoundationDB 官方镜像的内部布局，若上游变更库文件路径需同步调整。当前 `foundationdb/foundationdb:7.3.77` 镜像中该路径经验证存在。
- 无。