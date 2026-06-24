# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构与平台不匹配
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), is needed by, foundationdb-clients, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 平台标识，但 CI 构建宿主机为 `x86_64`（日志中 rustup 检测为 `x86_64-unknown-linux-gnu`，meson 确认 `Host machine cpu: x86_64`），且 openEuler 的 glibc 版本符号与 RHEL 9 不完全兼容，导致 RPM 依赖 `libm.so.6(GLIBC_2.17)(64bit)` 无法满足。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行为安装 FoundationDB 客户端的 RUN 指令。该指令的 RPM URL 硬编码了 `aarch64` 架构，同时该 RPM 是为 RHEL 9（`el9`）构建的，与 openEuler 基础镜像和 CI 构建宿主机的 x86_64 架构均不兼容。这是 PR 引入的新代码直接触发的失败。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载 URL 改为动态构造，根据当前构建架构（通过 `uname -m` 或 BuildKit 内置 ARG）选择对应的 `.x86_64.rpm` 或 `.aarch64.rpm`。同时，若 openEuler 上 FoundationDB RPM 的 glibc 依赖确实无法满足（el9 RPM 与 openEuler 不兼容），应改用 `--nodeps` 强制安装，或从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取二进制文件，绕过 RPM 依赖解析问题。

### 方向 2（置信度: 中）
若 FoundationDB 官方仅发布 `el9` 系 RPM（无 openEuler 原生包），可考虑不使用 RPM 安装，改为从 FoundationDB 源码编译安装，或使用 FoundationDB 官方提供的 Docker 镜像作为多阶段构建的源。

## 需要进一步确认的点
1. 需确认 FoundationDB 7.3.77 在 GitHub Releases 上是否提供了 `x86_64` / `amd64` 架构的 RPM（当前 URL 仅指定了 `aarch64`）
2. 需在 openEuler 24.03-lts-sp3 容器内验证 `rpm -ivh --nodeps foundationdb-clients-*.rpm` 后 FoundationDB 客户端是否能正常运行，以判断 glibc 版本差异是否仅影响 RPM 元数据还是实际 ABI 兼容性
3. 需确认 openEuler yum 仓库中是否有 FoundationDB 相关包可替代手动 RPM 安装

## 修复验证要求
若修复方向采用动态架构选择，code-fixer 必须在两个架构（x86_64 和 aarch64）的 openEuler 容器中分别验证 FoundationDB RPM 安装成功；若采用 `--nodeps` 方式，必须验证 `fdbcli --version` 能正常输出版本信息且无动态链接器错误。
