# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM glibc 符号版本不兼容
- 新模式症状关键词: Failed dependencies, GLIBC, libm.so.6, foundationdb-clients, is needed by, aarch64

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
    rpm -ivh /tmp/fdb-clients.rpm && \
    rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL ... && rpm -ivh ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
--------------------
ERROR: failed to solve: process ".../foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 上游发布的 RPM 包（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）是为 **RHEL9 / CentOS9** 构建的 aarch64 架构包，其二进制依赖 `libm.so.6(GLIBC_2.17)(64bit)` 需要 EL9 系列 glibc 提供的特定符号版本，而 openEuler 24.03 的 glibc 采用不同的符号版本管理方案，无法满足该 RPM 的依赖声明。

同时，日志显示当前 CI 构建运行于 **x86_64** 平台（Rust 安装日志: `default host triple is x86_64-unknown-linux-gnu`；fuse3 meson 日志: `Host machine cpu family: x86_64`），但 Dockerfile 第 22 行将 FoundationDB RPM 的下载 URL **硬编码为 `aarch64`**，存在架构与 RPM 不匹配的第二重问题。

### 与 PR 变更的关联
本次 PR 标题为 "Add 3FS Image"，核心变更是新增 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行全新文件）。该 Dockerfile 的所有构建步骤均为此 PR 首次引入，因此 **失败由 PR 变更直接触发**。失败的 `RUN` 步骤（FoundationDB RPM 安装）位于第 22-24 行，是该 Dockerfile 的第 5 个构建步骤（5/9）。

## 修复方向

### 方向 1（置信度: 高）— 改用多阶段构建从 FoundationDB 官方 Docker 镜像提取客户端二进制
放弃从 GitHub Releases 下载 RPM 的方式，改为多阶段构建：
- Stage 1: 使用 `foundationdb/foundationdb:7.3.77` 官方镜像作为源
- Stage 2: `COPY --from=...` 将 `fdbcli`、`libfdb_c.so` 等客户端所需的二进制和库文件复制到 openEuler 镜像中

此方法完全绕开 RPM 依赖冲突，借鉴历史模式 16（`RPM 包停止发布 → 换多阶段构建绕过`）的思路。

### 方向 2（置信度: 中）— 下载 FoundationDB 官方预编译 tarball 替代 RPM
FoundationDB 也提供 `.tar.gz` 格式的预编译二进制发布包（通常会包含所有架构）。使用 tar 包安装可以跳过 rpm 依赖检查。但仍然需要确认 tar 包内的二进制能在 openEuler 的 glibc 上正常运行，且需要处理架构选择逻辑。

### 方向 3（置信度: 低）— 从源码编译 FoundationDB 客户端
在 Dockerfile 中 `git clone` FoundationDB 源码并编译客户端部分。此方案规避了预编译二进制与 openEuler 的兼容性问题，但大幅增加构建时间和复杂度，且 FoundationDB 的构建依赖链较长。

## 需要进一步确认的点
1. FoundationDB 7.3.77 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`）是否提供所需客户端工具（`fdbcli`、`fdb_c` 库及其他 3FS 依赖的 FoundationDB 组件），以及镜像内的路径布局
2. FoundationDB 是否有适合 openEuler 24.03（基于其 glibc 版本）的预编译包（检查 GitHub Releases 是否有 `-linux-` 通用 tarball 而非 `-el9-` 专用 RPM）
3. 3FS 构建对 FoundationDB 客户端的具体需求——仅需要 `fdbcli` 和 `libfdb_c.so`，还是需要完整的 FDB 客户端库套件（如 `libfdb_java.so`、Python 绑定等）
4. PR 的 README 中标注支持的架构为 `amd64, arm64`，确认 CI 是否对两种架构均执行构建，并确认当前仅 x86_64 失败还是 aarch64 也会失败（aarch64 CI 日志未提供）

## 修复验证要求
若采用方向 1（多阶段构建），code-fixer 必须：
1. 确认 `foundationdb/foundationdb:7.3.77` 官方镜像的标签和内部路径在 PR 生成时仍然可用且未变更
2. 在 openEuler 24.03 容器中验证从官方镜像复制的 `fdbcli` 能正常运行（`ldd fdbcli` 确认无缺失的 .so 依赖）
3. 若方向 2 或方向 3，必须从 FoundationDB GitHub Releases 页面确认对应版本和架构的制品确实存在且能解压/运行
