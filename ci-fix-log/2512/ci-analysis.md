# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)(64bit) is needed by`, `aarch64.rpm`, `rpm -ivh`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而 CI 构建环境为 x86_64 架构。aarch64 RPM 依赖的 `libm.so.6(GLIBC_2.17)(64bit)` 在 x86_64 系统上无法满足，导致 `rpm -ivh` 失败。

### 与 PR 变更的关联
PR 直接引入了新的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行全新增），其中第 22 行将 FoundationDB RPM URL 硬编码为 aarch64 架构。该 Dockerfile 需要同时支持 x86_64 和 aarch64 两种架构的构建，但当前只考虑了 aarch64。这是 PR 引入的错误。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载 URL 从硬编码 aarch64 改为根据构建架构动态选择：x86_64 构建使用 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 构建使用 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。可使用 Buildx 的内置 `TARGETARCH` ARG 或 shell uname 检测来构造正确的 URL。

### 方向 2（置信度: 低）
若 FoundationDB 7.3.77 未提供 x86_64 RPM 包（需确认上游 release 页面），则该镜像可能仅支持 aarch64 架构，需在 Dockerfile 或 README 中明确标注架构限制，并在 image-info.yml 中调整 `Architectures` 字段。

## 需要进一步确认的点
1. 确认 FoundationDB 7.3.77 在 GitHub Releases 中是否同时发布了 x86_64 和 aarch64 的 RPM 包
2. 确认 3FS 项目对 FoundationDB 的版本要求是否固定为 7.3.77，或是否支持其他版本
3. 确认此镜像是否计划同时支持 amd64 和 arm64 两种架构（README 中标注了 `Architectures: amd64, arm64`）
