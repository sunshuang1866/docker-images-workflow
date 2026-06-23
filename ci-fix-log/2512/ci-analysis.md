# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: error: Failed dependencies, libm.so.6, GLIBC_2.17, rpm -ivh, foundationdb, aarch64 RPM on x86_64

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
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64`（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但 CI 本次构建运行在 x86_64 平台（日志确认：`Host machine cpu family: x86_64`，`default host triple is x86_64-unknown-linux-gnu`）。aarch64 架构的 RPM 在 x86_64 平台上安装时，其依赖 `libm.so.6(GLIBC_2.17)(64bit)` 无法通过 base image 的 rpm 依赖检查，导致 `rpm -ivh` 失败。

### 与 PR 变更的关联
此失败**直接由 PR 新增的 Dockerfile 引起**。该 Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`）是本次 PR 全新添加的文件（+69 行），其中第 22 行 FoundationDB 安装步骤的 RPM URL 写死了 `aarch64` 架构，未考虑 x86_64 平台的兼容性。当 CI 对 PR 触发 x86_64 架构构建时，该步骤必然失败。

注：历史模式知识库中已记录此 PR 经历过多次迭代修复（模式10、模式11、模式18），本次日志中的 FoundationDB RPM 失败是新的独立问题，之前的已修复问题在本次日志中未复现。

## 修复方向

### 方向 1（置信度: 高）
**将 FoundationDB RPM 下载 URL 改为架构感知**。FoundationDB 在 GitHub Releases 中为同一版本同时提供 `aarch64` 和 `x86_64` 的 RPM。Dockerfile 应使用 BuildKit 的 `BUILDARCH` 变量或手动架构检测（`uname -m` → 映射 → `x86_64` / `aarch64`），动态拼接正确的 RPM 文件名，而不是硬编码 `aarch64`。

### 方向 2（置信度: 中）
**验证 FoundationDB 是否支持在 openEuler 上通过 RPM 安装**。FoundationDB 官方 RPM 为 RHEL/CentOS el9 构建，其 RPM 依赖描述符（如 `libm.so.6(GLIBC_2.17)`）可能与 openEuler 24.03 的 glibc 版本标签体系存在兼容性差异。如果即使使用了正确架构的 RPM 仍然报依赖问题，则需改用 FoundationDB 官方 Docker 镜像的多阶段构建方案（参考模式16），或从源码编译 FoundationDB 客户端。

## 需要进一步确认的点
1. 确认 CI 是否同时构建 x86_64 和 aarch64 两个架构，以及本次失败是否仅出现在 x86_64 job 中（日志仅呈现了一个 job 的输出）。
2. 在 x86_64 的 openEuler 24.03 容器内，手动尝试安装 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，验证其依赖是否能在 openEuler 的 yum repo 中全部满足。若仍有依赖冲突，则方向 1 不足以解决问题，需采用方向 2。

## 修复验证要求
1. code-fixer 在修复后，必须在 x86_64 的 openEuler:24.03-lts-sp3 容器中执行完整的 `docker build`，验证 FoundationDB RPM 安装步骤通过。
2. 如果修复方案涉及架构条件分支，需同时在 aarch64 环境中验证构建通过，确保未破坏已有架构的兼容性。
3. 若改用 FoundationDB 官方 Docker 镜像多阶段复制方案（方向 2），code-fixer 需从 `foundationdb/foundationdb:7.3.77` 镜像中确认目标二进制文件及其 so 依赖路径后再提交。
