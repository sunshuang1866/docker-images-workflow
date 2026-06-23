# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 安装 URL 硬编码 aarch64 架构字符串，导致在 x86_64 CI 环境构建失败（无法跨架构安装 aarch64 RPM）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 共修复 4 处根因（已通过 fix 分支上的渐进式提交完成）

## 修复逻辑

CI 分析报告指出 4 项根因，当前 fix 分支均已修复：

1. **FoundationDB RPM 硬编码 aarch64**（CI 直接报错项）：将 `rpm -ivh foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 替换为多阶段构建方案 —— `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 后通过 `COPY --from=fdb` 获取 `fdbcli` 和 `libfdb_c.so`，同时通过 `curl` 下载架构无关的 `fdb-headers` tarball。该方案天然支持多架构，无需 TARGETARCH 条件判断。

2. **git clone --depth 1 + commit checkout 不兼容**：移除 `--depth 1`、`--shallow-submodules` 标志及静默吞错的 `|| true`，改为完整克隆后正常 checkout，失败时正确报错。

3. **clang 库路径硬编码 aarch64**：将路径中的字面量 `aarch64` 替换为 `$(uname -m)` 动态获取构建架构，映射为 `${ARCH}-openEuler-linux-gnu`，同时适用于 x86_64 和 aarch64。

4. **boost-foundation 包名不存在**：将运行时 yum install 中的 `boost-foundation` 移除，保留已验证可用的 `boost-filesystem boost-system boost-program-options`。

## 潜在风险
- 多阶段构建中的 `libfdb_c.so` 来自 FoundationDB 官方镜像（通常基于 Ubuntu），与 openEuler 的 glibc/openssl 等运行时库可能存在 ABI 兼容性差异。此为运行时问题，不影响 CI 构建通过，但建议在容器启动后验证 `fdbcli` 和 `libfdb_c.so` 可正常加载。
- `git clone` 改为完整克隆，3FS 仓库体积较大，会增加 CI 构建时间和网络流量。