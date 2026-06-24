# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 下载URL硬编码架构
- 新模式症状关键词: Failed dependencies, aarch64, rpm -ivh, foundationdb, libm.so.6

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构标识（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但当前 CI 构建运行在 **x86_64** 环境（日志中 rust 默认 host triple 为 `x86_64-unknown-linux-gnu`，fuse meson 检测 CPU 为 `x86_64`）。在 x86_64 系统上安装 aarch64 架构的 RPM 包时，rpm 无法在 x86_64 的 glibc 包中找到 aarch64 架构所需的 `libm.so.6(GLIBC_2.17)(64bit)` 能力，导致依赖解析失败。

### 与 PR 变更的关联
PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（新增文件）第 22 行直接引入了此错误。该行从 FoundationDB GitHub Releases 下载 RPM 包时，URL 中架构字段写死为 `aarch64`。而 CI 流水线会分别构建 x86_64 和 aarch64 两个架构的镜像，x86_64 构建任务因下载了错误的架构包而失败。此问题是本次 PR 变更直接导致的。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构标识改为动态引用 Docker BuildKit 的内置 `TARGETARCH` 变量（或 `BUILDARCH`），建立架构映射：
- Docker `amd64` / `x86_64` → RPM 文件名中的 `x86_64`
- Docker `arm64` → RPM 文件名中的 `aarch64`

在 Dockerfile 中使用 `ARG TARGETARCH` 声明后，通过 shell 条件（`if`/`case`）或变量映射来构造正确的下载 URL，确保 x86_64 构建下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 构建下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。

### 方向 2（置信度: 中）
如果 FoundationDB 不提供 x86_64 架构的 el9 RPM（仅发布 aarch64 版本），则需要考虑替代方案：从 FoundationDB 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`）中通过多阶段构建 `COPY --from` 提取 x86_64 的客户端二进制，或以源码编译方式替代 RPM 安装。

## 需要进一步确认的点
1. FoundationDB 7.3.77 GitHub Release 是否确实发布了 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`（需访问 https://github.com/apple/foundationdb/releases/tag/7.3.77 确认资产列表）。
2. FoundationDB 客户端二进制（`fdbcli`、`fdb_c` 等）在 3FS 构建中的实际用途——3FS 的 CMake 构建是否依赖 FoundationDB 的 C 客户端库（`libfdb_c.so`），还是仅需客户端命令行工具。
3. 当前 CI 失败日志仅展示了 x86_64 构建的失败，aarch64 构建可能成功也可能有其他独立错误。需获取 aarch64 构建 job 的日志进行独立分析。
