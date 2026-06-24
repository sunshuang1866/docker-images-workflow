# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM下载URL
- 新模式症状关键词: `error: Failed dependencies`, `foundationdb-clients`, `aarch64`, `el9`, `rpm -ivh`, GLIBC_2.17

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`（step 5/9，FoundationDB RPM 安装步骤）
- 失败原因: FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而实际构建运行在 x86_64 环境（rustup 日志确认 `default host triple is x86_64-unknown-linux-gnu`），导致 aarch64 RPM 在 x86_64 系统上依赖解析失败。

### 与 PR 变更的关联
PR 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行新文件），其中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构字符串。该 Dockerfile 声明支持 amd64 和 arm64 双架构（见 `Storage/3fs/README.md` 中的 `Architectures: amd64, arm64`），但 URL 未适配构建架构，导致 x86_64（amd64）构建必然失败。此失败由本次 PR 变更直接引入。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 从硬编码 `aarch64` 改为基于构建架构动态选择：使用 BuildKit 预定义变量 `TARGETARCH`（amd64/arm64）或 shell 命令 `$(uname -m)` 映射到 FoundationDB RPM 的架构后缀（x86_64 / aarch64），使同一 Dockerfile 在两种架构上均可正确下载对应 RPM。

### 方向 2（置信度: 中）
如果 openEuler 24.03-LTS-SP3 的 glibc/libm 确实不提供 `GLIBC_2.17` 符号版本（即使使用正确架构的 RPM），则需换用 FoundationDB 的静态链接版本或从 FoundationDB 官方 Docker 镜像中直接 `COPY` 二进制文件，绕过 RPM 依赖问题。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 x86_64 RPM（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）是否确实在 GitHub Releases 中可用，需验证其 URL 及依赖项在 openEuler 24.03-LTS-SP3 上是否可满足。
2. 即使架构问题修复后，`libm.so.6(GLIBC_2.17)` 符号在 openEuler 的 libm 中是否存在——若不存在，需进一步确认 openEuler 与 RHEL9 RPM 的 ABI 兼容性。
3. Dockerfile 中后续步骤（step 6/9：git clone + cmake 构建）还有两处已知问题记录在历史模式中（模式18：`--depth 1` 浅克隆与 commit hash checkout 不兼容；模式10：可能的构建依赖缺失），修复当前失败后这些后续步骤可能仍会阻塞。
4. 需获取 aarch64 构建节点的日志以对比确认：FoundationDB RPM 在 aarch64 CI 节点上是否也会因 glibc 符号问题失败，还是仅 x86_64 失败。

## 修复验证要求
code-fixer 在提交前必须：
1. 验证 FoundationDB 7.3.77 在 GitHub Releases 中同时提供了 x86_64 和 aarch64 两种 RPM 文件。
2. 在 openEuler 24.03-LTS-SP3 容器中分别测试 `rpm -ivh` 安装两种架构的 FoundationDB RPM，确认依赖均可满足。
3. 修复后需在两个架构上分别触发构建，确认 step 5/9 通过。
