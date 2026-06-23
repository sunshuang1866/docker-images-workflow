# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), foundationdb-clients, rpm -ivh, el9, aarch64

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
--------------------
ERROR: failed to solve: ...
Finished: FAILURE
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 客户端 RPM（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）是为 RHEL/CentOS 9 (EL9) 构建的，其 RPM 依赖 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 24.03 的 glibc/glibc RPM 元数据中不存在，导致 `rpm -ivh` 依赖解析失败。

### 与 PR 变更的关联
本次失败**完全由 PR 新增的 Dockerfile 引起**。PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行直接通过 RPM 安装 FoundationDB 客户端。该 RPM 存在两个问题：
1. **架构硬编码错误**：URL 和 RPM 包名使用了 `aarch64`，但当前构建环境实际运行在 `x86_64`（见 fuse 构建日志 `Host machine cpu: x86_64`，rustup 报告 `default host triple is x86_64-unknown-linux-gnu`）。即使绕过依赖问题，架构不匹配也会导致后续安装失败。
2. **跨发行版不兼容**：EL9 RPM 的 RPM 依赖元数据依赖 `libm.so.6(GLIBC_2.17)` 等 EL 系版本标签，openEuler 24.03 的 glibc 包不提供相同标签的 capability，`rpm` 工具直接拒绝安装。

其他步骤（yum 安装依赖、rustup 安装 Rust 工具链、fuse3 源码构建）均成功完成，失败仅发生在 FoundationDB RPM 安装步骤。

## 修复方向

### 方向 1（置信度: 高）
**改用 `--nodeps` 强制安装或直接解压 RPM 内容**，绕过 openEuler 上 RPM 依赖元数据不兼容的问题。因为 `libm.so.6` 本身在 openEuler 上一定存在（glibc 的一部分），只是 RPM capability 标签不匹配。可在 `rpm -ivh` 前加 `--nodeps`，或使用 `rpm2cpio` + `cpio` 手动解压二进制到目标路径。

### 方向 2（置信度: 高）
**将 RPM 架构选择改为动态判断**，根据 `$(uname -m)` 或 BuildKit 的 `TARGETARCH` 自适应选择 `x86_64` 或 `aarch64` 的 RPM 包，避免硬编码单架构。

### 方向 3（置信度: 中）
**从 FoundationDB 的 GitHub Release 同时拉取 x86_64 和 aarch64 的 RPM**，用 BuildKit `ARG TARGETARCH` 在构建时按架构选择对应 RPM，并结合 `--nodeps` 进行安装。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 EL9 RPM 除了 `libm.so.6(GLIBC_2.17)` 外，是否还有其他 EL9 特有的 RPM 依赖会在 `--nodeps` 后引起运行时问题（如 `libstdc++.so.6(GLIBCXX_3.4.21)` 等）。
2. FoundationDB 是否有官方 Docker 镜像可作为替代安装源（参考历史模式16 的多阶段构建方案）。
3. 此前知识库中已记录该 PR（模式10、模式18）存在其他构建问题（`boost-foundation` 包名、git 浅克隆与 commit hash checkout 不兼容），当前日志在 FoundationDB 步骤即中断，未能覆盖后续问题。修复 FoundationDB 步骤后可能仍需处理 git clone 步骤的问题。

## 修复验证要求
code-fixer 在提交前，必须使用与 CI 相同的基础镜像 `openeuler/openeuler:24.03-lts-sp3` 启动容器，手动执行 FoundationDB 安装步骤验证修复方案可行。建议同时验证 `--nodeps` 安装后 FoundationDB 客户端二进制（`fdbcli`）能否正常运行。
