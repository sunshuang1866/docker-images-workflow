# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构RPM依赖失败
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_`, `foundationdb-clients`, `aarch64`, `rpm -ivh`, `el9`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB clients RPM 下载 URL 硬编码为 `aarch64` 架构，但当前 CI 构建环境为 x86_64（日志中 Rust host triple 为 `x86_64-unknown-linux-gnu`，meson 检测 Host machine cpu family 为 `x86_64`）。`rpm -ivh` 安装 aarch64 RPM 时，系统无法提供 aarch64 架构的 glibc 依赖 `libm.so.6(GLIBC_2.17)(64bit)`，导致依赖解析失败。

### 与 PR 变更的关联
该 Dockerfile 为本 PR 全新新增的文件（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` added_lines: 69）。FoundationDB clients RPM 的安装逻辑由 PR 引入。URL 中硬编码 `aarch64` 未适配构建架构，直接导致构建失败。与历史知识库中该 PR 已有的模式18（git 浅克隆 + commit hash 不兼容）和模式10（运行时包名不存在、缺少构建依赖）不同，这是同一 PR 的一个独立的新问题。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 22 行 FoundationDB clients RPM 下载 URL 中的 `aarch64` 替换为 BuildKit 构建参数 `TARGETARCH`，根据实际构建目标架构动态选择正确的 RPM：
- x86_64 构建 → 下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64 构建 → 下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

### 方向 2（置信度: 中）
若 FoundationDB 官方未提供 openEuler 原生 RPM，考虑完全绕过 RPM 安装方式，改用多阶段构建从 FoundationDB 官方 Docker 镜像中 `COPY` 所需二进制文件，或从 FoundationDB 源码编译 clients 库。此方案可同时解决 `el9` RPM 与 openEuler 底层 glibc 版本的兼容性风险（当前 `el9` RPM 即使在匹配架构上安装成功，也可能与 openEuler 的 glibc soname 版本命名存在差异）。

## 需要进一步确认的点
1. **FoundationDB 官方是否提供 x86_64 RPM**：需确认 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 GitHub Releases 中确实存在且可下载。
2. **el9 RPM 在 openEuler 上的兼容性**：即使架构匹配，`el9`（RHEL 9 系）的 RPM 在 openEuler 上的 glibc 版本化符号可能仍不匹配。需要在实际容器中验证 `rpm -ivh --nodeps` 安装后 libfdb_c 是否能正常链接和运行。
3. **与模式18（git checkout 问题）的交互**：当前构建在第 5/9 步失败（FoundationDB RPM 安装），尚未执行到第 6/9 步（git clone + cmake 构建）。即使修复了 FoundationDB 问题，模式18 中记录的 `git clone --depth 1` + commit hash checkout 不兼容问题仍可能在下一步暴露，需一并处理。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（本次不涉及）
