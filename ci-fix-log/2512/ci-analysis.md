# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM不匹配
- 新模式症状关键词: Failed dependencies, libm.so.6, GLIBC_2.17, aarch64, rpm, foundationdb

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
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但 CI 构建运行在 x86_64 架构上（rustup 检测到 `x86_64-unknown-linux-gnu`），导致 RPM 依赖项无法在 x86_64 系统上得到满足。

### 与 PR 变更的关联
直接关联。该 Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`）是本次 PR 新增的文件，共新增 69 行。FoundationDB RPM 安装步骤的 URL 中未使用架构变量来动态选择 x86_64 或 aarch64 对应的 RPM 包，而是写死了 aarch64。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构字符串从硬编码的 `aarch64` 改为基于构建架构动态选择。FoundationDB 在 GitHub Releases 中同时提供 x86_64 和 aarch64 的 RPM 包（如 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）。需要在 RUN 步骤中使用 `BUILDARCH`（BuildKit 预定义变量）或 `$(uname -m)` 来构造正确的 RPM 文件名，使 x86_64 构建下载 x86_64 的 RPM，aarch64 构建下载 aarch64 的 RPM。

### 方向 2（置信度: 中）
除架构问题外，该 RPM 是为 el9（RHEL 9）构建的，即使架构匹配也可能在 openEuler 上遇到 glibc 版本符号不兼容问题。如果方向 1 修复后仍出现依赖错误，可能需要考虑从 FoundationDB 源码自行编译，或使用 FoundationDB 官方 Docker 镜像的多阶段构建来提取二进制文件。

## 需要进一步确认的点

1. **FoundationDB RPM 在 openEuler 上的兼容性**：即使修正了架构 URL，`el9` RPM 在 openEuler 24.03 上是否完全兼容需要实际验证。`libm.so.6(GLIBC_2.17)` 是一个基础 glibc 版本符号，openEuler 应该能提供，但 el9 RPM 可能还有其他 openEuler 未注册的依赖项。（GLIBC_2.17 是 2012 年标记的版本符号，openEuler 的 glibc 应远高于此，但 RPM 的 provides 机制可能需要额外确认。）

2. **后续构建步骤的潜在问题**（虽然构建未达到这些步骤，但 Dockerfile 中存在已知问题模式）：
   - **模式18**：第 31-32 行的 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 模式——浅克隆后无法 checkout 到特定 commit hash，`|| true` 会静默吞掉错误，导致构建继续但使用了错误的源码版本。
   - **模式10**：第 57 行的 `boost-foundation` 包名可能不在 openEuler 24.03-lts-sp3 仓库中，需要验证实际可用包名。

## 修复验证要求
code-fixer 必须验证 FoundationDB 7.3.77 在 openEuler 24.03-lts-sp3 上通过 RPM 安装的可行性——在修复架构 URL 后，使用目标基础镜像启动容器并执行修改后的安装命令，确认 RPM 所有依赖项均可在 openEuler yum 仓库中满足，或确认 `--nodeps` 安装后 FoundationDB 客户端库能正常工作。
