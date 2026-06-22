# 修复摘要

## 修复的问题
将 FoundationDB 客户端从硬编码 aarch64 RPM 下载/安装改为多阶段构建方式（`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb`），同时修复 `boost-foundation` 错误包名和 `git clone --depth 1` 与 commit checkout 冲突问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 新增 `ARG FDB_VERSION=7.3.77` 和多阶段构建 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`
  - 用 `COPY --from=fdb` 替代原来的 RPM 下载/安装步骤，从根本上消除架构硬编码问题
  - 移除 `yum install` 中的 `cpio`（不再需要 rpm2cpio 提取 RPM）
  - 移除 `git clone` 的 `--depth 1 --shallow-submodules` 参数，改为完整克隆以避免与后续 `git checkout ${VERSION}`（commit hash）冲突
  - 移除 `yum install` 运行依赖中的 `boost-foundation`（openEuler 中不存在此包名），仅保留 `boost-filesystem boost-system boost-program-options`
  - 新增 clang 库文件的架构感知符号链接（使用 `$(uname -m)`）
  - 修复 `libevent-devel` 缺失问题（添加到 build 依赖中）

## 修复逻辑

CI 分析报告指出三个根因：

1. **FoundationDB RPM 架构硬编码**（主因）：原 Dockerfile 使用 `curl` 下载 FoundationDB RPM 并 `rpm -ivh` 安装，URL 中硬编码了 `aarch64`，导致 x86_64 CI 环境构建失败。修复方案是采用多阶段构建：从官方 `foundationdb/foundationdb:${FDB_VERSION}` 镜像（支持多架构）COPY 所需的 `fdbcli` 和 `libfdb_c.so`，完全消除架构依赖问题。

   **验证结果**：已从 FoundationDB 7.3.77 GitHub Release 获取资产列表确认，基金会仅提供 `foundationdb-clients-7.3.77-1.el7.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，不存在 `el9.x86_64` RPM。这意味着即使修复架构选择逻辑，也需额外处理 EL7/EL9 差异。多阶段构建彻底规避了此问题。

2. **`boost-foundation` 包名错误**：openEuler 仓库中不存在 `boost-foundation` 包（此为 openSUSE 包名），已从运行依赖中移除。

3. **`git clone --depth 1` 与 commit hash checkout 冲突**：浅克隆（`--depth 1`）后无法检出任意 commit hash，改为完整克隆。

## 潜在风险
- FoundationDB 官方 Docker 镜像基于 CentOS/Debian，其 `libfdb_c.so` 需与 openEuler 24.03-lts-sp3 的 glibc 兼容。FoundationDB 7.3.77 客户端库通常是与 glibc 版本弱依赖的独立共享库，跨发行版兼容风险较低。若出现运行时链接错误，可考虑回退到 RPM 方式但需正确处理 EL7/EL9 架构映射。