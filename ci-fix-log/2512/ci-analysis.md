# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码不匹配
- 新模式症状关键词: error: Failed dependencies, rpm -ivh, aarch64, x86_64, libm.so.6, foundationdb-clients

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
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码了 `aarch64` 架构，而当前 CI 构建环境为 x86_64（日志中 rust 安装输出 `x86_64-unknown-linux-gnu`、fuse meson 检测 `Host machine cpu family: x86_64`），导致 x86_64 构建时安装了 aarch64 架构的 RPM 包，rpm 依赖解析报 `Failed dependencies`。

### 与 PR 变更的关联
该 Dockerfile 是本 PR 新增的文件（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 为 new_file），PR 引入了包含架构硬编码错误的 Dockerfile，直接触发了此构建失败。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中 FoundationDB RPM 下载 URL 的架构部分从硬编码 `aarch64` 改为根据 BUILDARCH/构建目标架构动态选择对应的 RPM 文件名（x86_64 使用 `x86_64` 架构的 RPM，aarch64 使用 `aarch64` 架构的 RPM）。可用 BuildKit 内置 ARG（如 `TARGETARCH`）或 shell 条件判断实现。

### 方向 2（置信度: 中）
若 FoundationDB 不提供 x86_64 RPM，考虑改用多阶段构建从 FoundationDB 官方 Docker 镜像中 `COPY --from` 对应的客户端二进制文件，替代 RPM 安装方式（参考模式16）。

### 方向 3（置信度: 中 — 潜在问题）
同一 Dockerfile 中 `git clone --recurse-submodules --depth 1` 后跟 `git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true` 存在模式18的浅克隆与 commit hash checkout 不兼容问题。当前构建在第10步（FoundationDB RPM）已失败，未到达 cmake 编译步骤，因此该问题尚未暴露，但后续修复 RPM 问题后可能遇到。

## 需要进一步确认的点
- FoundationDB 7.3.77 是否提供 x86_64 (amd64) 架构的 RPM 包，以及其确切的 URL 格式（检查 https://github.com/apple/foundationdb/releases/tag/7.3.77 上的发布文件列表）
- 该 Dockerfile 目标架构为 amd64 + arm64（README 中声明），需确认两个架构的 RPM 下载 URL 是否存在且可用
