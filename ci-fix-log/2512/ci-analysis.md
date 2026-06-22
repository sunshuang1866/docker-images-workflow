# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: `error: Failed dependencies`, `foundationdb-clients`, `aarch64.rpm`, `x86_64`, `GLIBC_2.17`, `rpm -ivh`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`（PR 新增文件）
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 的下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但当前 CI 构建运行在 x86_64 环境下（日志中 rust 安装输出 `default host triple is x86_64-unknown-linux-gnu`，meson 检测 `Host machine cpu family: x86_64`），导致 `rpm -ivh` 试图在 x86_64 系统上安装 aarch64 RPM 包，RPM 依赖检查因架构不匹配而失败。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 文件（69 行全新内容），其中该 RUN 步骤直接引入了硬编码 aarch64 RPM URL 的错误。此问题由本次 PR 变更直接触发。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载 URL 改为支持多架构。FoundationDB 在 GitHub Releases 上同时发布 `x86_64` 和 `aarch64` 的 RPM 包（URL 模式为 `foundationdb-clients-{VERSION}-1.el9.{arch}.rpm`）。Dockerfile 中需要通过架构检测（使用 `$(uname -m)` 或 BuildKit 的 `TARGETARCH` ARG）动态选择正确的 RPM URL，确保 x86_64 构建下载 `x86_64.rpm`，aarch64 构建下载 `aarch64.rpm`。

## 需要进一步确认的点
- FoundationDB 7.3.77 的 GitHub Releases 页面是否确实同时提供 x86_64 和 aarch64 两个架构的 RPM（URL 中的 `el9` 段在 x86_64 上是否一致）
- 该 Dockerfile 中是否还存在其他同样硬编码架构的下载 URL
- `historical_patterns` 中已记录的该 PR 的其他问题（模式10 的 `boost-foundation` 包名错误、模式18 的 `git clone --depth 1` 与 commit hash checkout 冲突）仍需一并修复

## 修复验证要求
code-fixer 在提交前必须：
1. 验证 FoundationDB 7.3.77 在 GitHub Releases 上确实存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`（而非仅有 aarch64 或使用不同命名约定）
2. 在 openEuler 24.03-lts-sp3 的 x86_64 容器中实际执行 `rpm -ivh` 验证该 RPM 可安装（无额外的 glibc 或其他依赖冲突）
3. 修复后确认 `#10 [5/9]` 步骤在 CI 的 x86_64 构建环境中通过
