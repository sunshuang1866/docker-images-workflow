# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: `error: Failed dependencies`, `aarch64`, `rpm -ivh`, `GLIBC`, `foundationdb-clients`

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
- 失败原因: FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构路径，但当前构建环境为 x86_64（日志中 Rust 安装 `x86_64-unknown-linux-gnu`，Meson 检测 `Host machine cpu family: x86_64`），aarch64 架构的 RPM 包无法在 x86_64 平台上安装，`rpm -ivh` 报依赖失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中的第 22-24 行硬编码了 `aarch64` 架构的 FoundationDB 客户端 RPM 下载 URL。该改动直接导致了此构建失败。若 CI 构建的是 x86_64 架构，需要对应使用 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`；若需同时支持多架构，应使用 BuildKit 内置的 `TARGETARCH` 变量动态选择正确的 RPM 文件。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 从硬编码的 `aarch64` 改为使用 BuildKit 的 `TARGETARCH` 变量动态构造架构字符串，使 Dockerfile 在 x86_64 和 aarch64 构建环境下均能正确下载对应架构的 RPM 包。例如，在 Dockerfile 中声明 `ARG TARGETARCH`，然后根据 `TARGETARCH` 的值选择 `x86_64` 或 `aarch64` 的 RPM URL。

## 需要进一步确认的点
- FoundationDB 7.3.77 是否发布了 x86_64 架构的 el9 RPM 包（在 GitHub Releases 页面确认 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 是否存在）。
- openEuler 24.03 的 glibc 版本（2.38 系列）与 FoundationDB 7.3.77 el9 RPM 的 glibc 2.17 依赖是否兼容；若 el9 的 RPM 包在 openEuler 上存在 glibc ABI 不兼容问题，可能需要改用 FoundationDB 的 tar.gz 二进制包安装方式（参考 `foundationdb-clients_7.3.77-1_amd64.tar.gz` 等通用包），或添加 `--nodeps` 安装后手动处理运行时库依赖。
- 日志显示构建在 FoundationDB RPM 安装步骤即失败，尚未到达 git clone 和 cmake 编译步骤，无法验证 Dockerfile 后续步骤（cmake 构建参数、库路径补丁、commit hash checkout 等）是否正确。修复 RPM 安装问题后，需持续观察后续步骤是否还有其他构建错误。
