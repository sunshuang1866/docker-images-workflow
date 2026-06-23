# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码
- 新模式症状关键词: `error: Failed dependencies`, `aarch64.rpm`, `libm.so.6(GLIBC_2.17)`, RPM 架构不匹配

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 客户端 RPM 下载 URL 中硬编码了 `aarch64` 架构，但当前 CI 构建环境实际为 `x86_64`（日志证据：Rust 安装为 `x86_64-unknown-linux-gnu`，meson 检测为 `Host machine cpu family: x86_64`），导致 `rpm -ivh` 尝试在 x86_64 系统上安装 aarch64 架构的 RPM 包，触发依赖不满足错误。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行全新文件），其中 `RUN curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 行硬编码了 `aarch64`。这是 PR 新增代码直接引入的 bug，与 PR 中其他 `.agents/` → `.claude/` 重命名无关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端 RPM 的下载 URL 从硬编码 `aarch64` 改为根据 BuildKit 内置 `TARGETARCH` 变量动态选择。FoundationDB 官方同时提供了 `x86_64` 和 `aarch64` 架构的 RPM 包，通过 `TARGETARCH` 映射到正确的架构字符串即可。注意还需要将 `rpm -ivh` 改为 `rpm -ivh --nodeps` 或先确认 `glibc` 版本兼容性，因为 `libm.so.6(GLIBC_2.17)` 在 openEuler 上的提供者可能与 FoundationDB RPM 的 RPM 依赖声明不完全匹配。

### 方向 2（置信度: 中）
如果 FoundationDB 不提供 x86_64 的 RPM 包，考虑改用多阶段构建从 FoundationDB 官方 Docker 镜像中 `COPY` 二进制文件，或从 FoundationDB 源码编译客户端库。但根据 FoundationDB GitHub releases 页面，`x86_64` 架构的 RPM 通常是可用的，方向 1 更为直接。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否确实发布了 `x86_64` 架构的 RPM（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`），需检查 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 的实际资产列表。
2. 历史模式中提及的 `git clone --depth 1` + commit hash checkout 不兼容问题（模式18）在当前日志中未触发（构建在此步骤前已失败），修复架构问题后该问题可能暴露，需一并处理：将 `git checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch origin ${VERSION}` 再 checkout。
3. 即使架构问题修复后，`libm.so.6(GLIBC_2.17)` 依赖声明可能与 openEuler 的 `glibc` 包提供的符号版本不完全一致，可能需要 `rpm -ivh --nodeps` 或预先确认兼容性。

## 修复验证要求
无。此问题涉及修改 Dockerfile 中的 URL 构造逻辑和包安装方式，不涉及正则 patch 外部源文件。
