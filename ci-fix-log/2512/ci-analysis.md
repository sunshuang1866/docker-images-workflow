# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM不兼容
- 新模式症状关键词: aarch64, rpm, Failed dependencies, libm.so.6(GLIBC_2.17), el9, foundationdb-clients

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

日志证据表明 CI 构建环境为 x86_64 架构：
- Step #8（Rust 安装）：`default host triple is x86_64-unknown-linux-gnu`
- Step #9（Fuse meson）：`Host machine cpu family: x86_64`

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构，同时该 RPM 是针对 `el9`（RHEL/CentOS 9）构建的，其 glibc 版本化符号 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 24.03 上不兼容，导致 `rpm -ivh` 安装失败。

### 与 PR 变更的关联
该 Dockerfile 为本次 PR 全新引入（`new_file: True`，共 69 行），失败 100% 由 PR 变更引起。Dockerfile 在 FoundationDB 客户端安装步骤中：
1. 未使用 BuildKit 的 `TARGETARCH` 或条件判断区分 x86_64 / aarch64 架构，始终下载 aarch64 版 RPM
2. RPM 本身为 `el9` 制品，与 openEuler 24.03 的 glibc 符号版本不兼容

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 安装逻辑改为架构感知：使用 BuildKit `ARG TARGETARCH` 或运行时 shell 判断 `$(uname -m)` 来动态选择正确的 RPM 下载 URL（x86_64 对应 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 对应 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）。同时需验证 FoundationDB 客户端 RPM 在 openEuler 24.03 上的实际可用性——el9 RPM 的 glibc 依赖可能与 openEuler 不兼容，必要时考虑从 FoundationDB 官方 Docker 镜像 `COPY` 二进制文件（类似模式16 的多阶段构建方案），或改用 `rpm --nodeps --force` 安装后手动验证功能完整性。

### 方向 2（置信度: 中）
如果 `el9` RPM 在所有架构上都与 openEuler glibc 不兼容，则改用多阶段构建：`FROM foundationdb/foundationdb:7.3.77 AS fdb-source`，然后 `COPY --from=fdb-source /usr/bin/fdbcli /usr/lib/libfdb_c.so* /path/` 将 FoundationDB 客户端库和二进制复制到 openEuler 镜像中。

## 需要进一步确认的点
- FoundationDB 7.3.77 的 x86_64 RPM 在 openEuler 24.03 上是否能通过 `rpm -ivh` 正常安装（无 glibc 符号不兼容问题）。如果同样报 glibc 依赖缺失，则需采用方向 2 的多阶段构建方案
- FoundationDB 官方是否提供非 el9 的通用 Linux 二进制包（如 `.tar.gz` 格式），作为 RPM 的替代安装方式

## 修复验证要求
- code-fixer 必须在 openEuler 24.03 容器中分别验证 x86_64 和 aarch64 两架构上 FoundationDB 客户端 RPM 或替代安装方案的实际可用性
- 修复后的 Dockerfile 需在 x86_64 CI runner 上通过 `docker build` 验证（当前 CI 基于 x86_64 runner），同时确认 aarch64 环境下也能构建成功（可通过 mock 或实际 aarch64 runner 验证 RPM URL 切换逻辑）
