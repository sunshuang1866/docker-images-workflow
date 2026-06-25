# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版依赖不兼容
- 新模式症状关键词: error: Failed dependencies, is needed by, rpm -ivh, el9, aarch64, foundationdb

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
--------------------
ERROR: failed to solve: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 是为 RHEL 9 (el9) aarch64 构建的 RPM 包，其声明的依赖 `libm.so.6(GLIBC_2.17)(64bit)` 无法被 openEuler 24.03-LTS-SP3 系统中已安装的 glibc 包满足——RPM 跨发行版依赖解析失败。同时 Dockerfile 将 RPM 架构硬编码为 `aarch64`，无法适配 amd64 构建目标。

### 与 PR 变更的关联
此 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新文件），其中第 22-24 行的 FoundationDB RPM 安装步骤是本次失败的直接触发点。该错误由本次 PR 的改动直接引入，非历史遗留问题。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 的 el9 RPM 包与 openEuler 发行版存在依赖声明不兼容。修复方向：
- 改用 FoundationDB 官方提供的其他安装方式（如解压式 tarball 而非 RPM），绕过 RPM 依赖解析
- 或使用 `rpm -ivh --nodeps` 跳过依赖检查后手动验证实际运行所需 .so 文件是否存在（仅在确认 openEuler 的 glibc 实际提供了所需符号版本时使用）

### 方向 2（置信度: 中）
将 FoundationDB RPM 的架构选择从硬编码 `aarch64` 改为根据 Docker 构建目标架构动态选择：
- 使用 Docker `TARGETARCH` 变量（需在 `FROM` 前声明 `ARG TARGETARCH`）构造正确的 RPM 下载 URL
- 同时需要解决方向 1 中的跨发行版依赖兼容问题，否则切换架构后仍可能失败

## 需要进一步确认的点
1. 当前 CI 日志是在 x86_64 还是 aarch64 构建节点上产生的？日志中 rustup 显示 `default host triple is x86_64-unknown-linux-gnu`，暗示构建节点为 x86_64，但目标基础镜像是 openEuler aarch64（通过 QEMU 仿真的跨架构构建）。需确认 CI 实际构建架构。
2. FoundationDB 7.3.77 是否提供适用于 openEuler 的 RPM 或其他安装包格式？需查阅 FoundationDB 官方发布页确认。
3. 即使 RPM 安装通过，Dockerfile 中还存在其他潜在问题（见下方"附加发现"），在修复当前错误后可能会依次暴露。

### 附加发现（本次 CI 日志未触发，但 PR diff 中可见的风险点）
- **git 浅克隆 + commit hash checkout**（Dockerfile 第 27-29 行）：`git clone --depth 1` 后 `git checkout ${VERSION} 2>/dev/null || true`，`|| true` 会静默掩盖 checkout 失败（参考历史模式 18）。
- **运行时包名**（Dockerfile 第 56 行）：`boost-foundation` 在 openEuler yum repo 中可能不存在（历史模式 10 已记录该问题）。

## 修复验证要求
- **方向 1（tarball 安装）**：code-fixer 必须验证 FoundationDB 7.3.77 官方是否提供 tarball 格式的发布包，并确认解压后的二进制文件在 openEuler 24.03-LTS-SP3 容器内可正常运行（`ldd` 检查所有 .so 依赖均已满足）。
- **方向 1（--nodeps）**：code-fixer 必须先在 openEuler 24.03-LTS-SP3 x86_64 和 aarch64 容器内验证 `rpm -ivh --nodeps` 安装后，`ldd` 检查 foundationdb-clients 的实际二进制是否能找到所有需要的 .so 文件，且运行时无 crash。
- **方向 2（动态架构）**：code-fixer 必须验证 FoundationDB 在两种架构（amd64/x86_64 和 arm64/aarch64）上均提供了对应 RPM 或安装包，并在两个架构上分别构建验证。
