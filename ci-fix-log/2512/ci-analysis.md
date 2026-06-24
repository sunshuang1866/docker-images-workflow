# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码下载URL
- 新模式症状关键词: `rpm -ivh`, `Failed dependencies`, `aarch64`, `GLIBC_2.17`, foundationdb-clients, 跨架构 RPM 安装

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
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: FoundationDB clients RPM 下载 URL 硬编码了 `aarch64` 架构，但当前 CI 构建运行在 `x86_64` 平台（rustup 检测到 `default host triple is x86_64-unknown-linux-gnu`），导致下载的 aarch64 RPM 无法在 x86_64 系统上安装 —— rpm 依赖检查无法为 aarch64 架构的包在 x86_64 主机上解析 `libm.so.6(GLIBC_2.17)(64bit)`。

### 与 PR 变更的关联
- 直接由本次 PR 新增的 Dockerfile 引起：`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 是本次 PR 全新添加的文件（+69 行），其中第 22-24 行的 FoundationDB 安装步骤硬编码了 `aarch64` 架构的 RPM URL。
- 该 Dockerfile 设计为多架构构建（README 标注 `Architectures: amd64, arm64`），但下载 URL 未参数化架构，导致 x86_64 CI job 必然失败。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 7.3.77 在 GitHub Releases 中同时提供 `x86_64` 和 `aarch64` 两种 RPM（URL 模式分别为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`）。应在 Dockerfile 中使用 BuildKit 内置 ARG（如 `TARGETARCH`）动态选择正确的架构 RPM URL，替代当前硬编码的 `aarch64` 字符串。

### 方向 2（置信度: 中）
若 FoundationDB RPM 仅在 aarch64 上可安装（EL9 与 openEuler 存在 glibc ABI 差异），可考虑从源码编译 FoundationDB clients，或使用 FoundationDB 官方 Docker 镜像进行多阶段构建 `COPY --from`。但复杂度更高，优先验证方向 1。

## 需要进一步确认的点

1. **FoundationDB RPM 在 openEuler x86_64 上的兼容性**：即使换为正确架构的 RPM（`x86_64`），FoundationDB 的 EL9 RPM 是否能在 openEuler 24.03-LTS-SP3 上正确安装（openEuler 与 RHEL 9 的 glibc 版本及 ABI 可能存在差异）。
2. **后续步骤是否还有其他架构硬编码**：CI 构建在步骤 5/9 即失败，步骤 6-9（git clone、cmake 编译、运行时包安装）未执行，无法确认是否存在其他问题。知识库中 模式18 提到 git `--depth 1` 浅克隆与 commit hash checkout 不兼容（在同一 Dockerfile 中），可能需要一并修复。
3. **yum 包可用性**：知识库 模式10 提到 `boost-foundation` 包名可能不存在于 openEuler，且原 `.claude/CLAUDE.md` 中曾列出 `clang-tools-extra`、`gmock-devel`、`gtest-devel`、`libdwarf-devel`、`gperftools-devel` 为 openEuler 上不存在的包，本次 PR 将这些包加入了 yum install 列表但当前日志中 yum 步骤显示 `Complete!`（步骤 7 通过），需在后续 CI 运行中持续验证。
4. **多架构 CI 覆盖**：当前日志仅展现了 x86_64 CI job 的失败，aarch64 CI job 的日志需要获取以确认 aarch64 上 FoundationDB 安装是否成功（URL 当前硬编码为 aarch64，该架构上可能通过此步骤）。

## 修复验证要求

code-fixer 必须：
1. 访问 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 确认 x86_64 RPM（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）确实存在且可公开下载。
2. 修复后在该项目的 openEuler 24.03-LTS-SP3 容器中验证 `rpm -ivh` 该 x86_64 RPM 能成功安装（依赖满足），或将 `rpm -ivh` 改为 `rpm -ivh --nodeps` 并手动验证二进制链接可用。
3. 修复 FoundationDB 步骤后应继续推进构建到后续步骤（git clone、cmake 编译），确认无阻塞性后续错误。
