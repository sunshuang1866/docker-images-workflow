# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构RPM硬编码
- 新模式症状关键词: Failed dependencies, libm.so.6(GLIBC_2.17), aarch64, .el9, rpm -ivh, foundationdb, hardcoded architecture

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL ... rpm -ivh /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端的 RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 发行版，二者均与 CI 构建环境的实际情况不兼容：(1) 日志中 Rust 工具链安装为 `x86_64-unknown-linux-gnu` 表明当前构建运行在 x86_64 平台，`aarch64.rpm` 架构不匹配；(2) `.el9` 包依赖 `libm.so.6(GLIBC_2.17)`，openEuler 24.03 的 glibc 版本/符号版本无法满足此依赖。

### 与 PR 变更的关联
PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（第 22-24 行）直接引入了该 RPM 安装步骤。此外，同一 Dockerfile 中第 35-40 行的 clang 库路径（`/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/`）也全部硬编码为 aarch64，与 FoundationDB RPM 属于同一类问题——整个 Dockerfile 仅针对单一架构编写，不具备跨架构适配能力。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端的 RPM 下载 URL 改为使用 BuildKit 内置 ARG（如 `TARGETARCH`）动态选择对应架构的 RPM 包。FoundationDB 在 GitHub Releases 中提供了 `x86_64` 和 `aarch64` 两种架构的 RPM。同时，将 clang 库路径的硬编码 `aarch64-openEuler-linux-gnu` 替换为基于 `TARGETARCH` 的条件分支（`x86_64` 对应 `x86_64-openEuler-linux-gnu`，`aarch64` 对应 `aarch64-openEuler-linux-gnu`）。

### 方向 2（置信度: 高）
如果 `el9` 版本的 FoundationDB RPM 在 openEuler 上持续存在 glibc 依赖不兼容问题（即架构匹配后仍因 `GLIBC_2.17` 符号缺失而失败），则改为从 FoundationDB 官方提供的其他格式（如 tar.gz 二进制包）安装，或通过源代码编译 FoundationDB 客户端库。FoundationDB GitHub Releases 页面同时提供 `.tar.gz` 格式的客户端包，可能无 RPM 依赖约束。

## 需要进一步确认的点
1. 需确认 FoundationDB 7.3.77 的 `el9.x86_64.rpm` 在 openEuler 24.03 x86_64 容器中是否同样存在 glibc 符号依赖问题；如存在，则需确认 `.tar.gz` 二进制包是否可直接使用。
2. 需确认 openEuler 24.03 上是否可以通过 `yum` 安装 `foundationdb-clients`（若 openEuler 仓库已收录该包，可完全绕过 GitHub Release 下载）。
3. Dockerfile 中所有硬编码 `aarch64` 路径（clang 库、FDB RPM）需逐一排查并改造为架构感知，不仅是 FoundationDB RPM 一处。

## 修复验证要求
code-fixer 在修复后，必须在 x86_64 和 aarch64 两个架构上分别执行 Docker build 验证：FoundationDB RPM 安装成功、clang 库软链接创建成功、整体 cmake 构建及 `cmake --build` 通过。不可仅在单一架构上测试。
