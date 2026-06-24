# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 架构硬编码错误
- 新模式症状关键词: `Failed dependencies`, `aarch64.rpm`, `x86_64`, `rpm -ivh`, foundationdb

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构，而 CI 构建运行在 `x86_64` 主机上（日志中 rust 安装为 `x86_64-unknown-linux-gnu`，meson 检测 CPU 为 `x86_64`），架构不匹配导致 RPM 依赖解析失败

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行，全新文件）。该 Dockerfile 第 22 行直接硬编码了 `aarch64` 架构的 FoundationDB RPM 下载 URL，未使用 BuildKit 的 `TARGETARCH`/`BUILDARCH` 变量做多架构适配。此问题由本次 PR 直接引入。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的 `aarch64` 替换为 BuildKit 内置变量 `${TARGETARCH}` 或 `${BUILDARCH}`，使构建能根据目标架构自动选择正确的 RPM 包。需确认 FoundationDB 7.3.77 在 GitHub Releases 中同时提供了 `x86_64` 和 `aarch64` 两种 RPM 制品。

### 方向 2（置信度: 中）
若 FoundationDB 7.3.77 未提供 `x86_64` RPM，则需改用其他架构兼容的安装方式（如从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取客户端二进制，类似历史模式 16 的做法）。

## 需要进一步确认的点
1. FoundationDB 7.3.77 GitHub Release 是否包含 `x86_64` 架构的 RPM（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）
2. 若 `x86_64` RPM 存在，`libm.so.6(GLIBC_2.17)` 依赖在 openEuler 24.03 的 x86_64 基础镜像中是否能被满足
3. 该 Dockerfile 后续步骤中还有多处硬编码 `aarch64` 路径（如第 40-43 行的 clang 库路径 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/` 和 `libclang_rt.builtins-aarch64.a`），这些也需要根据架构做条件适配

## 修复验证要求
code-fixer 在提交修复前，必须：
1. 验证 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 GitHub Releases 中确实存在且可下载
2. 在 openEuler 24.03-lts-sp3 x86_64 容器中验证该 RPM 可以正常安装（`rpm -ivh` 通过）
3. 检查 Dockerfile 中所有架构相关路径（clang 库路径、symlink 名称等）均已改为动态适配，而非只改 FoundationDB 一处
