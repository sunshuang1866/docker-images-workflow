# 修复摘要

## 修复的问题
FoundationDB RPM 在 openEuler 24.03 上安装时因 RPM 依赖元数据不兼容导致构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 移除 `curl` + `rpm -ivh` 安装 FoundationDB RHEL 9 RPM 的步骤（第22-24行，CI 直接报错位置）
  - 改用多阶段构建：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb` 提取 fdbcli 和 libfdb_c.so
  - 修复 `git clone` 中 `--depth 1` 浅克隆与 commit hash checkout 兼容性问题（移除 `--depth 1` 和 `|| true`）
  - 修复 `git -C fuse-3.16.1 meson setup build` 为正确路径

## 修复逻辑
采用 CI 分析报告方向 2（多阶段构建），从 FoundationDB 官方 Docker 镜像中直接复制客户端二进制文件（`fdbcli`、`libfdb_c.so`），完全绕过 RPM 安装步骤，避免了 RHEL 9 RPM 在 openEuler 上因 `libm.so.6(GLIBC_2.17)` 等 RPM provides 元数据不匹配导致的依赖解析失败。同时修复了 `git clone --depth 1` 浅克隆与 commit hash checkout 的不兼容问题（移除 `--depth 1` 和 `|| true` 掩盖的错误）。

## 潜在风险
- `foundationdb/foundationdb:7.3.77` 镜像需支持 aarch64 架构以匹配 openEuler 基础镜像架构，需在 CI 中实际构建验证。
- 从官方镜像 COPY 的文件路径（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`）依赖 FoundationDB 官方镜像的内部布局，若上游变更路径则需同步更新。