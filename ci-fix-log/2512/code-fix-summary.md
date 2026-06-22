# 修复摘要

## 修复的问题
将 FoundationDB 客户端二进制安装方式从 RPM 安装改为多阶段构建（`COPY --from`），解决 RPM 跨发行版依赖不兼容及硬编码架构问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 使用 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建，通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`，替代原来的 RPM 安装方式。

## 修复逻辑

**根因**：CI 分析报告指出两个问题——
1. FoundationDB `el9` RPM 依赖 `libm.so.6(GLIBC_2.17)` 版本化符号，该 RPM provides 在 openEuler 24.03-lts-sp3 的 glibc 包中不匹配，导致 `rpm -ivh` 失败
2. RPM 下载 URL 硬编码了 `aarch64` 架构，与 CI 实际运行的 `x86_64` 架构不匹配

**修复方案**：采用 CI 分析报告建议的 Direction 1（高置信度）——通过多阶段构建从 FoundationDB 官方容器镜像中提取二进制文件：
- `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` — 拉取官方 FoundationDB 镜像（已确认 `7.3.77` tag 在 Docker Hub 上存在且支持 amd64/arm64 双架构，镜像大小约 548 MB）
- `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` — 提取 FDB 命令行客户端
- `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so` — 提取 FDB C 客户端库

**正则验证**：无需正则 patch。从 FoundationDB 上游 Dockerfile（`https://raw.githubusercontent.com/apple/foundationdb/7.3.77/packaging/docker/Dockerfile`）确认文件路径正确——`fdbcli` 安装到 `/usr/bin/`，`libfdb_c.so` 安装到 `/usr/lib/`。

**优势**：
- 完全绕过 RPM 包管理器，避免跨发行版 RPM 依赖冲突
- Docker 根据构建平台自动选择对应架构的镜像（无需手动处理 `TARGETARCH`）
- 二进制文件在 FoundationDB 官方容器中已验证可运行

## 潜在风险
- FoundationDB 官方镜像中的二进制文件动态链接到 Rocky Linux 9.4 的 glibc（约 2.34），openEuler 24.03-lts-sp3 的 glibc 版本应兼容（≥ 2.34），但仍建议在目标环境中验证 `fdbcli --version` 能正常输出
- 多阶段构建会拉取完整的 FoundationDB 镜像（~548 MB），增加首次构建时间，但不影响最终镜像大小（COPY 仅提取所需文件）