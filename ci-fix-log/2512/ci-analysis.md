# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 硬编码架构URL
- 新模式症状关键词: `Failed dependencies`, `libm.so.6`, `rpm -ivh`, `aarch64`, architecture mismatch

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB clients RPM 下载 URL 硬编码了 `aarch64` 架构文件名，但构建宿主机架构为 `x86_64`（参见 `#9` 日志中 `Host machine cpu: x86_64` 及 `#8` 日志中 `default host triple is x86_64-unknown-linux-gnu`），导致 aarch64 RPM 安装时无法在 x86_64 系统上找到对应的 aarch64 库依赖 `libm.so.6(GLIBC_2.17)`，rpm 依赖检查失败。

### 与 PR 变更的关联
PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 第 22-24 行直接写死了 aarch64 架构的 RPM 下载 URL：
```
RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && ...
```
该 URL 中的 `aarch64` 未被替换为动态架构变量。当前 CI 构建触发的是 x86_64 架构构建，因此下载了错误的 RPM 包，触发了本次失败。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB clients RPM 下载 URL 中的架构部分从硬编码 `aarch64` 改为动态架构变量（如 BuildKit 预定义 ARG `TARGETARCH` 或 shell 的 `$(uname -m)` 映射），使 x86_64 构建下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，aarch64 构建下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`。

### 方向 2（置信度: 中）
考虑 FoundationDB clients RPM 是为 RHEL/CentOS (`.el9`) 构建的，openEuler 系统可能存在 glibc 符号版本差异。即使架构正确，EL9 RPM 在 openEuler 24.03 上也可能因 glibc 版本兼容性问题导致类似失败。可评估改用 FoundationDB 官方 Docker 镜像多阶段构建 `COPY --from` 方式获取 `fdbcli` 二进制，绕过 RPM 安装（类似模式16）。

## 需要进一步确认的点
- FoundationDB 7.3.77 EL9 x86_64 RPM 在 openEuler 24.03-LTS-SP3 上是否可直接安装（glibc 兼容性）
- 该 CI 构建是否也需要在 aarch64 架构上单独执行（`docker build --platform linux/arm64`），其日志是否已提供
- 若 aarch64 构建也已执行且成功，则本次失败仅限于 x86_64 架构 URL 错误

## 修复验证要求
code-fixer 修改 Dockerfile 中的架构变量逻辑后，必须在以下两个场景验证：
1. 验证 `https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 openEuler 24.03-LTS-SP3 x86_64 容器中 `rpm -ivh` 可成功安装
2. 若需支持 aarch64，同样验证 aarch64 RPM 在 openEuler 24.03-LTS-SP3 ARM64 容器中可成功安装
