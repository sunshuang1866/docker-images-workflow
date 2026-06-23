# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: error: Failed dependencies, libm.so.6, rpm -ivh, aarch64, x86_64, foundationdb

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但本次构建运行在 `x86_64` 平台上（日志中 Rust default host triple 为 `x86_64-unknown-linux-gnu`，FUSE meson 检测到 `Host machine cpu: x86_64`）。FoundationDB 同时提供 `x86_64` 和 `aarch64` 两种架构的 RPM，但 Dockerfile 未做架构检测和动态 URL 构造，导致在 x86_64 构建时下载并尝试安装 aarch64 架构的 RPM，引发依赖解析失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（共 69 行新代码），该文件的第 22-24 行即为本次失败的 FoundationDB RPM 安装步骤。该错误**由 PR 变更直接引入**——新增的 Dockerfile 中 RPM URL 未适配多架构构建。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中使用 BuildKit 预定义 ARG `TARGETARCH`（值为 `amd64`/`arm64`）或 `dpkg --print-architecture` / `uname -m` 检测当前构建平台架构，将 FoundationDB RPM URL 中的 `aarch64` 替换为动态架构值。FoundationDB release 页面中 x86_64 架构的 RPM 文件名为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 架构为 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。需在 RUN 块开头声明 `ARG TARGETARCH` 使 BuildKit 变量可用，并建立 `amd64 → x86_64`、`arm64 → aarch64` 的架构名映射。

### 方向 2（置信度: 中）
即便修正架构匹配后，FoundationDB `el9`（RHEL/CentOS 9）RPM 在 openEuler 24.03-LTS-SP3 上仍可能存在其他依赖不兼容问题（如不同的 `libm.so.6` 符号版本、不同的包命名体系）。若架构修正后仍有依赖失败，可考虑：改用 FoundationDB 官方 Docker 镜像做多阶段构建（`COPY --from`），或从 FoundationDB 源码编译安装。

## 需要进一步确认的点
- FoundationDB `el9` RPM 在 openEuler 24.03-LTS-SP3 x86_64 平台上是否存在其他依赖冲突（`libm.so.6(GLIBC_2.17)` 理论上 openEuler 应满足，但需实际验证）
- 多架构构建流水线中，x86_64 和 aarch64 是否分别在各自对应的 worker 上构建（当前日志仅展示了 x86_64 worker 的失败，aarch64 worker 的日志未提供）

## 修复验证要求
code-fixer 在提交修复前，必须在 openEuler 24.03-LTS-SP3 容器中分别验证：
1. x86_64 架构：下载并安装 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，确认 `rpm -ivh` 成功且无其他依赖缺失
2. aarch64 架构：下载并安装 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，同样确认安装成功
