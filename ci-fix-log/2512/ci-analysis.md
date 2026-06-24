# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `aarch64.rpm`, `rpm -ivh`, FoundationDB, 架构不匹配

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ... rpm -ivh /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm .../foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: FoundationDB clients RPM URL 中硬编码了 `aarch64` 架构标识，但当前 CI 构建 job 运行在 x86_64 架构上（日志确认：`rustup` 步骤输出 `default host triple is x86_64-unknown-linux-gnu`，`fuse` 构建输出 `Host machine cpu: x86_64`）。aarch64 RPM 包的 glibc 依赖无法在 x86_64 系统上满足，`rpm -ivh` 因依赖检查失败而退出。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该 Dockerfile 第 22 行硬编码了 `aarch64` 架构的 FoundationDB RPM 下载 URL（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）。该 Dockerfile 是多架构镜像（README 标注 `| amd64, arm64 |`），但未使用 `$(uname -m)` 或 BuildKit `TARGETARCH` 进行架构自适应，导致在 x86_64 构建 job 上直接使用了 aarch64 专用 RPM。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM URL 从硬编码 `aarch64` 改为架构自适应：使用 `$(uname -m)` 将架构名映射为 FoundationDB RPM 命名约定中的架构标识（x86_64 → `x86_64`，aarch64 → `aarch64`），通过 shell 变量拼接构造正确的下载 URL。

注意 FoundationDB 的 RPM 命名中 x86_64 架构标识为 `x86_64`（非 `amd64`），aarch64 为 `aarch64`，与 `uname -m` 输出一致，可直接使用。

## 需要进一步确认的点
1. FoundationDB 是否确实发布了 x86_64 版本的 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`（需验证 GitHub Release 页面中存在该文件）
2. `libm.so.6(GLIBC_2.17)` 依赖失败除架构因素外，是否还存在 openEuler 24.03-LTS-SP3 的 glibc 版本与 FoundationDB RPM 编译环境（RHEL/CentOS 9）不兼容的问题。如果架构修正后仍报 glibc 依赖错误，则需要考虑从 FoundationDB 源码编译而非安装 RPM
3. 即使修复当前 FoundationDB RPM 步骤，后续 cmake 构建步骤（Dockerfile 第 35-48 行）中 `git clone --depth 1` + `git checkout ${VERSION}`（VERSION=22fca04 为 7 字符 commit hash）的组合可能因浅克隆无法访问历史提交而静默失败（`2>/dev/null || true` 掩盖错误），参见知识库模式18
