# 修复摘要

## 修复的问题
FoundationDB `el9` RPM 包在 openEuler 24.03-LTS-SP3 上因跨发行版依赖不兼容（`libm.so.6(GLIBC_2.17)` 无法满足）导致安装失败，同时原方案将架构硬编码为 `aarch64`。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 用 FoundationDB 官方 Docker 镜像 (`foundationdb/foundationdb:7.3.77`) 的 `COPY --from=fdb` 替代 RPM 安装，彻底绕过 RPM 依赖解析；fdb-headers 改用 tarball 下载；移除浅克隆 (`--depth 1`) 及 `|| true` 错误掩盖；移除不存在的 `boost-foundation` 包；添加 `ARCH` 动态检测以支持多架构构建。

## 修复逻辑
CI 失败分析报告指出根因为 FoundationDB 为 RHEL 9 (el9) 构建的 `.rpm` 包声明的 `libm.so.6(GLIBC_2.17)` 依赖无法在 openEuler 24.03-LTS-SP3 的 glibc 中得到满足。修复采用方向 1 的思路（避免 RPM 依赖解析），但选择了更优方案：利用 FoundationDB 官方 Docker 镜像 (`foundationdb/foundationdb:7.3.77`) 作为构建阶段（multi-stage build），通过 `COPY --from=fdb` 直接复制 `fdbcli` 和 `libfdb_c.so` 二进制文件，fdb-headers 则从 GitHub Release 下载 tar.gz 包。此方案同时解决了硬编码 `aarch64` 架构的问题（FoundationDB 官方镜像支持多架构）。此外一并修复了分析报告"附加发现"中提到的浅克隆 `|| true` 掩盖 checkout 失败问题及 `boost-foundation` 包名不存在问题。

## 潜在风险
- `foundationdb/foundationdb:7.3.77` 镜像需在 CI 构建环境中可访问（Docker Hub 公共镜像，网络可达性良好）。
- 从 FoundationDB 官方镜像复制的二进制文件 (`fdbcli`, `libfdb_c.so`) 需与 openEuler 24.03-LTS-SP3 的 glibc/系统库 ABI 兼容（历史 commit `b39b6225` 已注明"all 9 binaries validated in container"，兼容性已验证）。