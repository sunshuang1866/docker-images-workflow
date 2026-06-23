# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）在 openEuler 24.03 上因跨发行版 RPM 依赖元数据不兼容（`libm.so.6(GLIBC_2.17)` capability 标签不存在）导致 `rpm -ivh` 失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 引入多阶段构建 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，通过 `COPY --from=fdb` 获取 `fdbcli` 和 `libfdb_c.so`，彻底消除 RPM 安装步骤
  2. 改用 GitHub Release tarball 下载 FoundationDB C 头文件（`fdb-headers-${FDB_VERSION}.tar.gz`），避免 RPM 依赖检查
  3. 移除运行时 yum install 中不存在的 `boost-foundation` 包
  4. 添加 clang 库符号链接以支持 CMake 交叉编译标志
  5. 修复 fuse 构建命令（`git -C` 改为 `cd && meson`）、curl/wget 添加重试参数、修复 `${HOME}` 为 `/root` 等稳定性改进

## 修复逻辑
CI 分析报告根因：FoundationDB 官方 RPM 为 RHEL/CentOS EL9 构建，其 RPM 元数据声明的依赖 capability（如 `libm.so.6(GLIBC_2.17)(64bit)`）在 openEuler 24.03 的 glibc RPM 中不存在，`rpm` 工具的依赖解析直接拒绝安装。

修复方案采用多阶段构建替代 RPM 安装：
- `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` — 从 FoundationDB 官方 Docker 镜像获取编译好的二进制文件，该镜像为多架构（x86_64/aarch64）镜像，由 Docker BuildKit 自动按目标平台拉取匹配架构
- `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` — 直接复制 CLI 二进制，不经过 RPM 依赖检查
- `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` — 复制 C 客户端动态库到 openEuler x86_64 标准库路径
- 头文件通过 tarball（非 RPM）从 GitHub Release 下载，同样不涉及 RPM 依赖解析

此方案同时解决了 CI 分析报告中指出的两个关联问题：
1. **跨发行版 RPM 不兼容** — COPY 指令不执行 RPM 依赖检查
2. **架构硬编码** — Docker 多阶段构建自动处理架构匹配

## 潜在风险
- FoundationDB 官方 Docker 镜像中 `libfdb_c.so` 链接的 EL 系系统库（如 `libstdc++`）可能与 openEuler 24.03 存在 ABI 差异，需在容器运行时验证 `fdbcli --version` 和 3FS 链接 `libfdb_c.so` 后的功能
- 根文件系统已于 openEuler 24.03 宿主编译验证，但若 CI 在 `aarch64` 平台运行，FoundationDB Docker 镜像需确认支持 `linux/arm64` 架构
- 由于 CI 日志在 FoundationDB 步骤中断，后续 git clone + cmake 构建步骤尚未经 CI 验证，但当前 Dockerfile 已移除浅克隆（`--depth 1`），使用完整 `git clone --recurse-submodules`，与 cmake checkout commit hash 兼容