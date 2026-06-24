# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM URL
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6`, `aarch64`, `rpm -ivh`, `foundationdb-clients`, architecture mismatch

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但 CI 当前执行的是 x86_64 架构构建任务（日志中 Rust 报告 `x86_64-unknown-linux-gnu`，meson 报告 `Host machine cpu family: x86_64`），导致 `rpm -ivh` 因架构不匹配而依赖解析失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该 Dockerfile 第 22-24 行在所有架构上均使用固定的 aarch64 RPM URL。该 URL 仅在 aarch64 构建环境中可安装，在 x86_64 上必然失败。此外，该 RPM 源自 EL9（Enterprise Linux 9），与 openEuler 24.03 的 glibc 版本是否兼容也需验证。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中引入架构条件判断（利用 BuildKit 的 `ARG TARGETARCH`），根据 `TARGETARCH` 值（`amd64` 或 `arm64`）构造正确的 FoundationDB RPM 下载 URL。FoundationDB 7.3.77 在 GitHub Releases 同时提供 x86_64 和 aarch64 两种 RPM：
- x86_64: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64: `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

### 方向 2（置信度: 中）
如果 FoundationDB 的 EL9 RPM 与 openEuler 24.03 存在更底层的 glibc 或 ABI 不兼容（`libm.so.6(GLIBC_2.17)` 版本符号问题可能不仅是架构导致，还可能是 OS 发行版差异），考虑从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取客户端二进制，或从 FoundationDB 源码编译安装。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 EL9 RPM 在 openEuler 24.03（aarch64）上是否确实可安装（目前 x86_64 失败掩盖了 aarch64 上 OS 兼容性的验证）。
2. aarch64 构建 job 的独立日志（若存在），确认 aarch64 侧是否有其他依赖问题。
3. Dockerfile 中后续步骤（git clone `--depth 1` + commit hash checkout with `|| true`）存在模式18已知隐患——即使 FDB 步骤修复，该步骤也可能因浅克隆无法 checkout 指定 commit hash 而静默失败，需一并修正。
