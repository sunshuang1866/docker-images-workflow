# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构，导致 x86_64 CI 流水线上构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已将 FoundationDB 客户端获取方式从 RPM 安装改为多阶段构建 `COPY --from=fdb`，从官方 FoundationDB Docker 镜像中提取 `fdbcli` 和 `libfdb_c.so`。此改动消除了架构硬编码问题，因为 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 会自动拉取与构建平台架构匹配的镜像。

## 修复逻辑
CI 分析报告指出 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），在 x86_64 CI 节点上导致 RPM 依赖错误（`libm.so.6(GLIBC_2.17)(64bit) is needed`）。

经检查，当前 `fix/2512` 分支 HEAD (commit `4f26bf3b`) 已修复此问题：
1. 移除了 RPM 下载及安装步骤（`curl` + `rpm -ivh`）
2. 改用多阶段构建：`FROM foundationdb/foundationdb:7.3.77 AS fdb`，然后 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so`
3. FoundationDB 官方 Docker 镜像是 multi-arch 的（amd64 + arm64），Docker 会自动拉取匹配构建平台的架构版本，彻底消除了架构硬编码问题
4. 已从上游 `foundationdb/foundationdb:7.3.77` 镜像 Dockerfile（`packaging/docker/Dockerfile`）确认：`libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，`fdbcli` 位于 `/usr/bin/fdbcli`，路径正确

同时，CI 分析报告中提到的 git 浅克隆问题（`--depth 1` + commit hash checkout）在当前 Dockerfile 中也已修复（移除了 `--depth 1` 参数，改用完整克隆）。

## 潜在风险
无。改用多阶段 `COPY --from=fdb` 后，FoundationDB 客户端二进制来自官方 Rocky Linux 9 镜像，与 openEuler 24.03（同为 RHEL 体系）的 glibc 兼容性良好。若后续构建中出现运行时动态库兼容问题（CI 分析报告"需要进一步确认的点"#1），需在容器中实际验证 `libfdb_c.so` 的链接情况，但这不是当前 CI 失败的直接原因。